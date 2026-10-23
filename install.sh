#!/bin/bash
set -e

# Configuration
UUID="gptouch@fraz0815.de"
EXT_DIR="$HOME/.local/share/gnome-shell/extensions/$UUID"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "-------------------------------------------------------"
echo "   GpTouch GNOME Extension - Installer"
echo "-------------------------------------------------------"

# 1. System Check: GNOME Version / gdctl
if ! command -v gdctl &> /dev/null; then
    echo "[ERROR] 'gdctl' command not found."
    echo "        This extension requires GNOME 48 or newer (Wayland)."
    exit 1
fi

# 2. System Check: Supported Terminal Emulator
if ! command -v ptyxis &> /dev/null && \
   ! command -v kgx &> /dev/null && \
   ! command -v gnome-terminal &> /dev/null && \
   ! command -v xdg-terminal-exec &> /dev/null; then
    echo "[WARN] No supported terminal emulator found (ptyxis, kgx, gnome-terminal)."
    echo "       Please install one of them so the extension can run the calibration script."
fi

# 3. System Check: User in 'input' group
if ! id -nG "$USER" | grep -qw "input"; then
    echo "[WARN] User '$USER' is not in the 'input' group."
    echo "       Run: sudo usermod -aG input $USER (requires re-login)."
fi

# 4. Prepare target directory
echo "[INFO] Creating directory: $EXT_DIR"
mkdir -p "$EXT_DIR"

# 5. Copy files
echo "[INFO] Copying extension files..."
if [ -d "$REPO_DIR/gnome-extension/$UUID" ]; then
    cp "$REPO_DIR/gnome-extension/$UUID/extension.js" "$EXT_DIR/"
    cp "$REPO_DIR/gnome-extension/$UUID/metadata.json" "$EXT_DIR/"
else
    echo "[ERROR] Directory 'gnome-extension/$UUID' not found!"
    exit 1
fi

echo "[INFO] Copying main script (gptouch.py)..."
cp "$REPO_DIR/gptouch.py" "$EXT_DIR/"
chmod +x "$EXT_DIR/gptouch.py"

# 6. Enable extension
echo "[INFO] Enabling extension..."
if gnome-extensions enable "$UUID" 2>/dev/null; then
    echo "[OK] Extension enabled."
else
    echo "[INFO] Extension registered. It will be available after the next login."
fi

echo "-------------------------------------------------------"
echo "[OK] Installation completed successfully."
echo "-------------------------------------------------------"
echo "IMPORTANT: Under Wayland, GNOME Shell requires you to"
echo "log out and log back in to load newly installed"
echo "extensions. Afterwards, make sure it is enabled via:"
echo "  gnome-extensions enable $UUID"
echo "-------------------------------------------------------"
