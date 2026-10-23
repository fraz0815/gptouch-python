## Touchscreen Rotation and Calibration Script for GNOME (Wayland)

> **Note:** This tool is intended primarily for **external or built-in touchscreens that do not have integrated orientation sensors**. It manually sets the display rotation and touchscreen calibration matrix.

This Python script offers a reliable terminal interface to automatically rotate the display and persistently calibrate the touchscreen input matrix in **Wayland environments**. It uses the modern **`gdctl`** utility (GNOME 48 - 51+) for display configuration and `libinput` for the touchscreen matrix, bypassing deprecated tools like `gnome-randr`.

---

## Requirements

The script is strictly intended for use under **Wayland** (GNOME 48 or newer).

### Dependencies

- **Python 3**
- **`gdctl`** (Part of GNOME / Mutter; for persistent display rotation)
- **`libinput`** (for Wayland input management and calibration)
- **`udevadm`** (part of `systemd` / `udev`)
- User must be in the **`input` group** (see Installation)
- `sudo` permissions for writing udev rules and reloading the driver
- A supported terminal emulator for the GNOME Extension: `ptyxis`, `kgx` (GNOME Console), `gnome-terminal`, or `xdg-terminal-exec`

---

## Installation

### 1. Install Dependencies

| Distribution | Command |
| :--- | :--- |
| **Debian / Ubuntu** | `sudo apt-get install python3 libinput-tools` |
| **Arch Linux** | `sudo pacman -S python libinput` |
| **Fedora** | `sudo dnf install python3 libinput` |

### 2. Add User to the `input` Group

To execute `libinput` operations without needing `sudo`, add your user to the `input` group. **A re-login is required.**

| Distribution | Command |
| :--- | :--- |
| **Debian / Ubuntu** | `sudo usermod -a -G input YOUR_USERNAME` |
| **Arch / Fedora** | `sudo usermod -aG input YOUR_USERNAME` |

---

## Usage

Clone the repository and run the script:

```bash
git clone https://github.com/fraz0815/gptouch-python.git
cd gptouch-python
python3 gptouch.py
```

### Interactive Mode

Simply run `python3 gptouch.py` and follow the on-screen prompts.

### Command Line Arguments (Non-Interactive)

You can use flags to skip prompts, making it suitable for mapping to keyboard shortcuts or custom scripts:

```bash
-o, --orientation 1: Landscape, 2: Portrait (Right), 3: Portrait (Left), 4: Inverted
--skip-reboot
--skip-gdm
```

### How it Works

1. **Detection:** Identifies the active logical monitor and its current scale via `gdctl show`, and locates the touchscreen device node via `libinput list-devices`.
2. **Rotation:** Uses `gdctl set --persistent --transform ...` to rotate the visual display while preserving your current display scaling.
3. **Calibration:** Calculates the matching `LIBINPUT_CALIBRATION_MATRIX` and writes a persistent rule to `/etc/udev/rules.d/99-touchscreen-orientation.rules`.
4. **Hot-Reload:**
   - Reloads udev rules (`udevadm control --reload-rules`).
   - Temporarily unbinds and rebinds the touchscreen kernel driver in `sysfs` to apply the new calibration matrix immediately without rebooting.
5. **GDM Sync:** Checks if `~/.config/monitors.xml` exists and optionally copies it to the system-wide GDM configuration path (`/etc/xdg/monitors.xml` on GNOME 49+, or `/var/lib/gdm/.config/` / `/var/lib/gdm3/.config/` on GNOME 48).

---

## GNOME Shell Extension (Optional but Recommended)

This repository includes a GNOME Shell Extension (compatible with GNOME 48 - 51) that adds a convenient drop-down menu to your top panel for quick display and touchscreen rotations with a single click.

We provide an automated script to install and enable the extension on your system.

Open your terminal and navigate to the cloned repository:

```bash
cd gptouch-python
```

Make the installation script executable:

```bash
chmod +x install.sh
```

Run the installer:

```bash
./install.sh
```

**Important (Wayland):** GNOME Shell does not allow hot-reloading extensions under Wayland. You must log out and log back in for the changes to take effect.

Once logged back in, the extension will be active and you will see the rotation icon in your top panel!

---

## License

This project is licensed under the MIT License.
