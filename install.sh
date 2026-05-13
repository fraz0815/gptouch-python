#!/bin/bash

# Configuration
UUID="gptouch@fraz0815.github.com"
EXT_DIR="$HOME/.local/share/gnome-shell/extensions/$UUID"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "-------------------------------------------------------"
echo "   GpTouch GNOME Extension - Installer"
echo "-------------------------------------------------------"

# 1. System Check: GNOME Version / gdctl
if ! command -v gdctl &> /dev/null; then
    echo "❌ Error: 'gdctl' command not found."
    echo "   This extension requires GNOME 48 or newer (Wayland)."
    exit 1
fi

# 2. System Check: GNOME Console (kgx)
if ! command -v kgx &> /dev/null; then
    echo "⚠️  Warning: 'kgx' (GNOME Console) not found."
    echo "   The extension is pre-configured to use 'kgx'."
    echo "   Please install 'kgx' or modify extension.js to use your preferred terminal."
fi

# 3. Prepare target directory
echo "📁 Creating directory: $EXT_DIR"
mkdir -p "$EXT_DIR"

# 4. Copy files
echo "📝 Copying extension files..."
if [ -d "$REPO_DIR/gnome-extension/$UUID" ]; then
    cp "$REPO_DIR/gnome-extension/$UUID/extension.js" "$EXT_DIR/"
    cp "$REPO_DIR/gnome-extension/$UUID/metadata.json" "$EXT_DIR/"
else
    echo "❌ Error: Directory 'gnome-extension/$UUID' not found!"
    exit 1
fi

echo "🐍 Copying main script (gptouch.py)..."
cp "$REPO_DIR/gptouch.py" "$EXT_DIR/"

# 5. Enable extension
echo "⚙️  Enabling extension..."
gnome-extensions enable "$UUID" 2>/dev/null || echo "   (Extension will be enabled after the next login)"

echo "-------------------------------------------------------"
echo "✅ Installation completed successfully!"
echo "-------------------------------------------------------"
echo "IMPORTANT: Since you are using Wayland, you must log"
echo "out and log back in for GNOME to fully load the new"
echo "extension and display the icon in your top panel."
echo "-------------------------------------------------------"
