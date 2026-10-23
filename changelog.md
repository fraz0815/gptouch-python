## [Unreleased] - 2026-10-23

### Added
- **GNOME 51 Support:** Added official compatibility for GNOME Shell 51 in `metadata.json`.
- **Expanded Terminal Support:** Added support for `ptyxis` and `xdg-terminal-exec` alongside `kgx` and `gnome-terminal` in the GNOME Shell Extension and `install.sh`.
- **Scale Preservation:** `gptouch.py` now parses and preserves the active monitor's current fractional or integer scaling factor (`--scale`) when applying display rotations via `gdctl`.
- **Desktop Notifications:** Added error notifications (`Main.notifyError`) to the extension if no supported terminal emulator is found.

### Changed
- **Extension Subprocess Handling:** Replaced deprecated `GLib.spawn_command_line_async` with `Gio.Subprocess` and `menu.addAction` in `extension.js` for safer execution without shell string parsing.
- **Improved Hardware Detection:** Refined `gdctl show` parsing to prioritize active displays under the `Logical monitors:` section and hardened `libinput` capability matching to explicitly exclude touchpads.
- **Subprocess Reliability:** Enforced `LC_ALL=C` across external command calls (`gdctl`, `libinput`, `udevadm`, `gnome-shell`) to ensure locale-independent regex parsing.
- **Cleaner CLI & Documentation:** Removed emojis from `gptouch.py`, `install.sh`, and `README.md` in favor of standard `[INFO]`, `[OK]`, `[WARN]`, and `[ERROR]` status prefixes.
- **Refactored Root File Writes:** Replaced `shell=True` pipes and external `echo` processes with native Python `stdin` (`input=`) handling for `sudo tee` operations and switched fallback `udevadm trigger` to `--action=change`.


8/14/2026

Refactor touchscreen detection, should be more reliable


5/14/2026

Updated metadata to 50

added install.sh for gnome-extension


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
