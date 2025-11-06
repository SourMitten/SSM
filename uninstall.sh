#!/usr/bin/env bash
# uninstall.sh — removes Sour System Monitor (SSM)
# Automatically detects and cleans up installed files

APP_PATH="/usr/local/bin/ssm"
PKG_DIR="/usr/local/bin/ssm_pkg"
CONFIG_DIR="$HOME/.config/ssm"

echo "=== Uninstalling Sour System Monitor (SSM) ==="

# Check if anything is installed
if [[ ! -f "$APP_PATH" && ! -d "$PKG_DIR" && ! -d "$CONFIG_DIR" ]]; then
    echo "SSM does not appear to be installed on this system."
    exit 0
fi

# Remove launcher
if [[ -f "$APP_PATH" ]]; then
    sudo rm -f "$APP_PATH"
    echo "Removed $APP_PATH"
fi

# Remove package directory
if [[ -d "$PKG_DIR" ]]; then
    sudo rm -rf "$PKG_DIR"
    echo "Removed $PKG_DIR"
fi

# Remove user config directory (optional)
if [[ -d "$CONFIG_DIR" ]]; then
    rm -rf "$CONFIG_DIR"
    echo "Removed user config directory at $CONFIG_DIR"
fi

rm dir -rf ./SSM/.git
rm -f ./SSM/.gitignore
rm -f ./SSM/install.sh
rm -f ./SSM/README.md
rm -f ./SSM/requirements.txt
rm -f ./SSM/ssm
rm dir -rf ./SSM/ssm_pkg
echo "=== SSM successfully uninstalled ==="
rm -- "$0"
