🚀 Added

GNOME Shell Extension (3/26)

Native gdctl Integration: The script now uses the gdctl tool introduced in GNOME 48 for display management.

Hot-Reloading: Implementation of a "driver-rebind" mechanism. The script restarts the kernel driver for the touchscreen so that calibration changes take effect instantly (no reboot required anymore).

CLI Arguments: Added support for command-line arguments (e.g., -o 2, --skip-reboot) to enable usage in scripts or via keyboard shortcuts.

GDM Automation: The script automatically detects the GNOME version and copies the monitor configuration to the correct directory for the login screen (distinguishes between /var/lib/gdm and the new /etc/xdg standard in GNOME 49+).

Increased Robustness: Improved error detection (e.g., checking if user is in the input group) and use of shutil for faster dependency checks.

⚡ Changed

Installation: Rust/Cargo and gnome-randr dependencies have been removed. Installation is now much leaner (only Python & libinput-tools).

Logging: Emojis have been replaced with text-based tags (e.g., [SUCCESS], [ERROR]) to avoid display errors in minimal TTY consoles.

Path Handling: Intelligent resolution of sysfs paths when rebinding drivers.

🗑️ Removed

X11 Support: Complete removal of legacy X11 code in favor of a clean Wayland architecture.

gnome-randr: Removed as a dependency (replaced by gdctl).
