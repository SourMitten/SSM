# SSM - Sour CLI System Monitor
**Version 1.1.0 (UniDionysus)**

A beautiful, real-time command-line system monitor built with Python and the `rich` library. SSM provides live, color-coded metrics for your system's CPU, Memory, Disk, and GPU usage, alongside a top processes list, disk partition preview, and an integrated network speedtest.

---

## ✨ Features
- **Real-time Resource Monitoring**: Live-updating progress bars for CPU, RAM, Disk, and GPU usage.
- **Top Processes**: Displays the top 10 most CPU-intensive processes with their PID, name, and resource consumption.
- **Disk Preview**: Overview of all mounted disk partitions and their usage percentages.
- **Network Speedtest**: Built-in download and upload speed testing with animated progress bars.
- **Interactive Controls**: Freeze the display, run a speedtest, or kill resource-heavy processes directly from the CLI.

---

## 📦 Dependencies
- `psutil`
- `py-cpuinfo`
- `pynvml`
- `rich`
- `keyboard`
- `speedtest-cli`

---

## 🚀 Installation

### 🪟 Windows
1. Ensure Python 3 is installed and added to your system's PATH.
2. Open your terminal and install the required dependencies:
   ```cmd
   python3 -m pip install -r requirements.txt
   ```
3. Create a shortcut to `main.py` on your desktop for quick and easy access. Double-click the shortcut to run the monitor.

### 🐧 Linux (Ubuntu / Debian-based)
1. Install the required Python dependencies via pip:
   ```bash
   pip3 install psutil py-cpuinfo pynvml rich keyboard speedtest-cli --break-system-packages
   ```
   or
   ```bash
   pip3 install -r requirements.txt
   ```
   **OR** use **Option 1: LNFinal (SSM Setup)** in [UBAutoSetup](https://github.com/SourMitten/UBAutoSetup) to handle dependencies automatically.

3. Run the installation script to install the `ssm` command globally:
   ```bash
   sudo bash install.sh
   ```

4. Once installed, you can access the program from **anywhere** in your terminal by running:
   ```bash
   sudo ssm
   ```
   *(Note: `sudo` is required because the `keyboard` library and process-killing features require root privileges on Linux.)*

---

## 🎮 Controls
While the program is running, use the following keyboard shortcuts:

| Key | Action |
| :--- | :--- |
| `Ctrl + C` | Exit the program gracefully. |
| `k` | Open the process killer prompt to terminate a selected process from the top processes list. |
| `n` | Trigger a network speedtest (Download & Upload). |
| `f` | Freeze / Unfreeze the live display (useful for reading process details). |

---

## ⚠️ Notes
- **Linux Permissions**: Running `sudo ssm` is mandatory on Linux systems to allow low-level hardware access and process management. 

---

## 📜 License & Credits
Created by SourMitten.  
For automated Linux setup, check out [UBAutoSetup](https://github.com/SourMitten/UBAutoSetup).

*Enjoy monitoring your system in style!* 🎨💻
