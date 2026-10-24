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

Verify that `gdctl` is available — if the command is missing, your GNOME is older
than 48 and this tool will not work:

```bash
gdctl show
```

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

| Flag | Meaning |
| :--- | :--- |
| `-o`, `--orientation` | `1` Landscape, `2` Portrait (right side up), `3` Portrait (left side up), `4` Inverted |
| `--skip-reboot` | Do not offer to reboot if the hot-reload of the touch driver failed |
| `--skip-gdm` | Do not ask about the login screen |

Example for a keyboard shortcut or a script: `python3 gptouch.py -o 2 --skip-gdm --skip-reboot`

**Run it as your normal user, not with `sudo`.** `gdctl` talks to your running
Mutter session over D-Bus, which is not available in a root environment; the
script calls `sudo` itself only for writing the udev rule and rebinding the
driver.

### How it Works

1. **Detection:** Identifies the active logical monitor and its current scale via `gdctl show`, and locates the touchscreen device node via `libinput list-devices`.
2. **Rotation:** Uses `gdctl set --persistent --transform ...` to rotate the visual display while preserving your current display scaling.
3. **Calibration:** Calculates the matching `LIBINPUT_CALIBRATION_MATRIX` and writes a persistent rule to `/etc/udev/rules.d/99-touchscreen-orientation.rules`.
4. **Hot-Reload:**
   - Reloads udev rules (`udevadm control --reload-rules`).
   - Temporarily unbinds and rebinds the touchscreen kernel driver in `sysfs` to apply the new calibration matrix immediately without rebooting.
5. **GDM Sync:** Checks if `~/.config/monitors.xml` exists and optionally copies it to the system-wide GDM configuration path (`/etc/xdg/monitors.xml` on GNOME 49+, or `/var/lib/gdm/.config/` / `/var/lib/gdm3/.config/` on GNOME 48).

### The Calibration Matrix It Writes

libinput reads `LIBINPUT_CALIBRATION_MATRIX` only when a device is *added*, which
is why changing input settings in a GUI under Wayland never helps. The script
therefore writes a persistent udev rule. The hand-written equivalent, if you
prefer to manage it yourself:

```
# /etc/udev/rules.d/99-touchscreen-orientation.rules
ATTRS{name}=="WACF2DTM", ENV{LIBINPUT_CALIBRATION_MATRIX}="0 1 0 -1 0 1"
```

Find your device name with `libinput list-devices`. Matrices used by the script,
written as `a b c d e f` and applied as `x' = a·x + b·y + c`, `y' = d·x + e·y + f`:

| Orientation | `gdctl --transform` | libinput matrix |
| :--- | :--- | :--- |
| 1 Landscape (normal) | `normal` | `1 0 0 0 1 0` |
| 2 Portrait (right side up) | `270` | `0 1 0 -1 0 1` |
| 3 Portrait (left side up) | `90` | `0 -1 1 1 0 0` |
| 4 Inverted | `180` | `-1 0 1 0 -1 1` |

Display transform and matrix always come from the same table, so they cannot get
out of sync. If portrait ends up rotated the wrong way on your panel, choose the
other portrait option.

### Reverting

Delete the rule, restore the display orientation, and reboot so the device is
re-added without the property:

```bash
sudo rm /etc/udev/rules.d/99-touchscreen-orientation.rules
sudo udevadm control --reload-rules
python3 gptouch.py -o 1 --skip-gdm
```

Keep your own custom rules in a differently named file — this one is overwritten
on every run.

---

## Troubleshooting

- **`gdctl` not found** — GNOME is older than 48, or you are on an X11 session
  (`echo $XDG_SESSION_TYPE`). X11 is no longer supported.
- **Display not detected** — run `gdctl show` by hand and compare. With several
  monitors the script uses the first logical monitor it finds (see Limitations).
- **Touchscreen not found** — run `libinput list-devices`. If it lists nothing,
  add yourself to the `input` group and log back in.
- **Touch still offset after rotating** — the matrix did not reach the device.
  Check it with `udevadm info -a -n /dev/input/eventX | grep -i calib`, and
  confirm the name in the rule matches the device name exactly.
- **Touchscreen unresponsive after the hot-reload** — the unbind/rebind did not
  come back. Replug the device or reboot; the display transform is unaffected.

## Limitations

- **One monitor, one touchscreen.** Only the first active logical monitor and the
  first `touch`-capable device (that is not a touchpad) are handled.
- **The udev rule matches on the device name**, so it can match more than one
  node, or none at all after a kernel update renames the device.
- **The GDM target path is inferred** from the GNOME major version, not from what
  GDM actually reads on your distro. [`gdm-settings`](https://github.com/gdm-settings/gdm-settings)
  does the same job graphically if the copy lands in the wrong place.
- **Not needed for devices with an orientation sensor.** Convertibles that already
  rotate correctly on their own gain nothing from this tool.

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

**Terminal requirement:** the menu starts the script inside a terminal window,
because `sudo` has to ask for a password there. It uses the first of `ptyxis`,
`kgx` (GNOME Console), `gnome-terminal` or `xdg-terminal-exec` that it finds, and
shows a notification if none of them is installed.

**Important (Wayland):** GNOME Shell does not allow hot-reloading extensions under Wayland. You must log out and log back in for the changes to take effect.

Once logged back in, the extension will be active and you will see the rotation icon in your top panel!

---

## License

This project is licensed under the MIT License.
