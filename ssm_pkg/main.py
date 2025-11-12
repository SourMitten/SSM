#!/usr/bin/env python3
import psutil
import time
import socket
import threading
import subprocess
from datetime import timedelta
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.style import Style
import keyboard

console = Console()

# ---------------- Global State ----------------
prev_net = None
prev_time = None
kill_requested = False
freeze_requested = False
speedtest_toggle = False
speedtest_running = False
speedtest_result_text = ""
speedtest_error = None
speed_samples = []
speed_samples_lock = threading.Lock()

# ---------------- Key Listeners ----------------
def listen_for_kill():
    global kill_requested
    while True:
        keyboard.wait("k")
        kill_requested = True

def listen_for_freeze():
    global freeze_requested
    while True:
        keyboard.wait("f")
        freeze_requested = not freeze_requested

def listen_for_speedtest_toggle():
    global speedtest_toggle
    while True:
        keyboard.wait("n")
        speedtest_toggle = not speedtest_toggle
        if speedtest_toggle:
            run_speedtest_background()

# ---------------- Helper Functions ----------------
def get_color(value: float) -> str:
    if value < 50:
        return "green"
    elif value < 80:
        return "yellow"
    else:
        return "red"

def format_bytes_per_sec(bps: float) -> str:
    kb = bps / 1024
    mb = kb / 1024
    gb = mb / 1024
    if gb >= 1:
        return f"{gb:.2f} GB/s"
    elif mb >= 1:
        return f"{mb:.2f} MB/s"
    elif kb >= 1:
        return f"{kb:.2f} KB/s"
    else:
        return f"{bps:.0f} B/s"

def get_system_stats():
    global prev_net, prev_time
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    net = psutil.net_io_counters()
    boot_time = psutil.boot_time()
    uptime_seconds = int(time.time() - boot_time)
    uptime = str(timedelta(seconds=uptime_seconds)).split('.')[0]
    hostname = socket.gethostname()

    now = time.time()
    if prev_net and prev_time:
        dt = now - prev_time
        if dt > 0:
            sent_rate = (net.bytes_sent - prev_net.bytes_sent) / dt
            recv_rate = (net.bytes_recv - prev_net.bytes_recv) / dt
        else:
            sent_rate = recv_rate = 0
    else:
        sent_rate = recv_rate = 0

    prev_net = net
    prev_time = now

    return {
        "cpu": cpu,
        "mem_used": mem.percent,
        "disk_used": disk.percent,
        "net_sent_rate": sent_rate,
        "net_recv_rate": recv_rate,
        "uptime": uptime,
        "hostname": hostname
    }

def get_top_processes(limit=10):
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            procs.append(p.info)
        except psutil.NoSuchProcess:
            continue
    procs = sorted(procs, key=lambda p: p['cpu_percent'], reverse=True)
    return procs[:limit]

# ---------------- Layout ----------------
def create_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=4),
        Layout(name="bars", size=6),
        Layout(name="network", size=3),
        Layout(name="bottom")
    )
    layout["bottom"].split_row(
        Layout(name="processes", ratio=60),
        Layout(name="disk_preview", ratio=40)
    )
    return layout

def build_bars(stats):
    cpu_color = get_color(stats["cpu"])
    mem_color = get_color(stats["mem_used"])
    disk_color = get_color(stats["disk_used"])

    cpu_bar = Progress(
        "[bold blue]CPU   ",
        BarColumn(bar_width=None, complete_style=Style(color=cpu_color)),
        TextColumn("{task.percentage:>3.0f}%")
    )

    mem_bar = Progress(
        "[bold magenta]Memory",
        BarColumn(bar_width=None, complete_style=Style(color=mem_color)),
        TextColumn("{task.percentage:>3.0f}%")
    )

    disk_bar = Progress(
        "[bold yellow]Disk  ",
        BarColumn(bar_width=None, complete_style=Style(color=disk_color)),
        TextColumn("{task.percentage:>3.0f}%")
    )

    cpu_bar.add_task("CPU", total=100, completed=stats["cpu"])
    mem_bar.add_task("Memory", total=100, completed=stats["mem_used"])
    disk_bar.add_task("Disk", total=100, completed=stats["disk_used"])

    bars_table = Table.grid(expand=True)
    bars_table.add_row(cpu_bar)
    bars_table.add_row(mem_bar)
    bars_table.add_row(disk_bar)
    return bars_table

def build_network_table(stats):
    net_table = Table.grid(expand=True)
    net_table.add_column("Upload", justify="right")
    net_table.add_column("Download", justify="right")
    net_table.add_row(
        format_bytes_per_sec(stats["net_sent_rate"]),
        format_bytes_per_sec(stats["net_recv_rate"])
    )
    return Panel(net_table, title="Network Info", style="bold green")

def build_process_table(top_procs):
    proc_table = Table(expand=True, show_header=True, header_style="bold cyan")
    proc_table.add_column("No.", justify="right")
    proc_table.add_column("PID", justify="right")
    proc_table.add_column("Name")
    proc_table.add_column("CPU %", justify="right")
    proc_table.add_column("Memory %", justify="right")

    for i, p in enumerate(top_procs, 1):
        proc_table.add_row(
            str(i),
            str(p["pid"]),
            p["name"][:20] if p["name"] else "N/A",
            f"{p['cpu_percent']:.1f}",
            f"{p['memory_percent']:.1f}"
        )
    return proc_table

def build_disk_preview():
    disks = psutil.disk_partitions(all=False)
    table = Table(expand=True, show_header=True, header_style="bold magenta")
    table.add_column("Device")
    table.add_column("Mountpoint")
    table.add_column("FS Type")
    table.add_column("Used %", justify="right")

    for d in disks:
        try:
            usage = psutil.disk_usage(d.mountpoint)
            table.add_row(
                d.device,
                d.mountpoint,
                d.fstype,
                f"{usage.percent:.0f}%"
            )
        except PermissionError:
            continue

    return Panel(table, title="Disk Preview", style="bold yellow")

def build_speedtest_panel():
    with speed_samples_lock:
        graph_line = "".join("█" if x > 0 else " " for x in speed_samples[-50:])
        text = speedtest_result_text if speedtest_result_text else "(running...)" if speedtest_running else "(not started)"
        error = f"[red]{speedtest_error}[/red]" if speedtest_error else ""
    panel_content = Text(graph_line + "\n" + text + "\n" + error)
    return Panel(panel_content, title="Speedtest Panel", style="bold magenta", expand=True)

def render_layout(layout, stats, top_procs):
    header_text = Text(
        f"Sour CLI Sys Monitor — {stats['hostname']} | Uptime: {stats['uptime']}",
        style="bold green"
    )
    commands_text = Text(
        "Commands: Ctrl+C = Exit | k = Kill | n = Speedtest | f = Freeze",
        style="bold cyan"
    )
    layout["header"].update(Panel(header_text + "\n" + commands_text, style="bold white"))
    layout["bars"].update(build_bars(stats))
    layout["network"].update(build_network_table(stats))
    layout["processes"].update(build_process_table(top_procs))
    layout["disk_preview"].update(build_disk_preview())
    if speedtest_toggle:
        layout["network"].update(build_speedtest_panel())

# ---------------- Kill Process ----------------
def kill_proc_tree(pid):
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            child.kill()
        parent.kill()
        psutil.wait_procs(children, timeout=3)
    except Exception as e:
        console.print(f"[red]Error killing process: {e}[/red]")

def kill_process_prompt(top_procs, live):
    live.stop()
    console.clear()
    console.print("[bold yellow]Kill a process[/bold yellow]")
    for i, p in enumerate(top_procs, 1):
        console.print(f"[cyan]{i}[/cyan]: {p['name']} (PID {p['pid']}) CPU {p['cpu_percent']:.1f}%")
    try:
        console.print()
        choice = int(console.input("[bold white]Enter process number to kill (0 to cancel): [/bold white]"))
        if choice == 0:
            console.print("[yellow]Canceled.[/yellow]")
        else:
            proc = top_procs[choice - 1]
            kill_proc_tree(proc["pid"])
            console.print(f"[green]Killed {proc['name']} (PID {proc['pid']})[/green]")
    except:
        console.print("[red]Invalid selection[/red]")
    finally:
        time.sleep(1)
        live.start()

# ---------------- Speedtest Integration ----------------
def run_speedtest_background():
    global speedtest_running, speedtest_result_text, speedtest_error, speed_samples
    if speedtest_running:
        return

    def _worker():
        global speedtest_running, speedtest_result_text, speedtest_error, speed_samples
        speedtest_running = True
        speedtest_result_text = ""
        speedtest_error = None
        with speed_samples_lock:
            speed_samples = []

        try:
            proc = subprocess.Popen(
                ["speedtest-cli", "--simple"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
        except FileNotFoundError:
            speedtest_error = "speedtest-cli not found."
            speedtest_running = False
            return
        except Exception as e:
            speedtest_error = f"Failed to start speedtest-cli: {e}"
            speedtest_running = False
            return

        last = psutil.net_io_counters()
        last_time = time.time()

        try:
            for line in proc.stdout:
                line = line.strip()
                if line:
                    with speed_samples_lock:
                        speedtest_result_text += line + "\n"

                now = time.time()
                cur = psutil.net_io_counters()
                dt = max(now - last_time, 1e-6)
                down_bps = (cur.bytes_recv - last.bytes_recv) / dt
                up_bps = (cur.bytes_sent - last.bytes_sent) / dt
                sample_mbps = max(down_bps, up_bps) * 8.0 / 1_000_000.0
                with speed_samples_lock:
                    speed_samples.append(sample_mbps)
                    if len(speed_samples) > 200:
                        speed_samples = speed_samples[-200:]
                last = cur
                last_time = now
        except Exception as e:
            speedtest_error = f"Speedtest error: {e}"

        proc.wait(timeout=10)
        speedtest_running = False

    t = threading.Thread(target=_worker, daemon=True)
    t.start()

# ---------------- Main ----------------
def main():
    global prev_net, prev_time, kill_requested

    prev_net = psutil.net_io_counters()
    prev_time = time.time()

    # Start key listeners
    threading.Thread(target=listen_for_kill, daemon=True).start()
    threading.Thread(target=listen_for_freeze, daemon=True).start()
    threading.Thread(target=listen_for_speedtest_toggle, daemon=True).start()

    layout = create_layout()
    with Live(layout, refresh_per_second=2, screen=True) as live:
        try:
            while True:
                stats = get_system_stats()
                top_procs = get_top_processes()

                if not freeze_requested:
                    render_layout(layout, stats, top_procs)

                if kill_requested:
                    kill_requested = False
                    kill_process_prompt(top_procs, live)

                time.sleep(0.2)

        except KeyboardInterrupt:
            console.print("\n[red]Exiting Sour CLI Sys Monitor...[/red]")

if __name__ == "__main__":
    main()
