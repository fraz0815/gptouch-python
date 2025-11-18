## 🖥️ Touchscreen Rotation and Calibration Script for GNOME (Wayland)

> **Note:** This tool is intended primarily for **external or built-in touchscreens that do not have integrated orientation sensors**. It manually sets the display rotation and touchscreen calibration matrix.

This Python script offers a reliable terminal interface to automatically rotate the display and persistently calibrate the touchscreen input matrix in **Wayland environments**. It uses the modern **`gdctl`** utility (GNOME $\geq 48$) for display configuration and `libinput` for the touchscreen matrix, bypassing deprecated tools like `gnome-randr`.

-----

## 🛠️ Requirements

The script is strictly intended for use under **Wayland** (GNOME).

### 🛑 Dependencies

  * **Python 3**
  * **`gdctl`** (Part of GNOME; for persistent display rotation)
  * **`libinput`** (for Wayland input management and calibration)
  * User must be in the **`input` group** (see Installation).
  * `sudo` permissions for writing udev rules.

-----

## 📥 Installation

### 1\. Install Dependencies

| Distribution Type | Command |
| :--- | :--- |
| **Debian/Ubuntu** | `sudo apt-get install python3 libinput-tools` |
| **Arch** | `sudo pacman -S python libinput` |
| **Fedora** | `sudo dnf install python3 libinput` |


### 2\. Add User to the `input` Group

To execute `libinput` operations without needing `sudo`, add your user to the `input` group. **A re-login is required.**

| Distribution Type | Command |
| :--- | :--- |
| **Debian/Ubuntu** | `sudo usermod -a -G input YOUR_USERNAME` |
| **Arch/Fedora** | `sudo usermod -aG input YOUR_USERNAME` |

-----

## 💡 Usage

Clone the repository and run the script:

```bash
git clone https://github.com/fraz0815/gptouch-python.git
cd gptouch-python
python3 gptouch.py
```

### Interactive Mode

Simply run `python3 gptouch.py`.

### Command Line Arguments (Non-Interactive)

You can use flags to skip prompts, making it perfect for mapping to keyboard shortcuts or rotation scripts.

```bash
-o, --orientation 1: Landscape, 2: Portrait (Right), 3: Portrait (Left), 4: Inverted
--skip-reboot
--skip-gdm
```

### How it Works

1. Detection: Identifies the active monitor via `gdctl show`  and the touchscreen device path via `libinput`.

2. Rotation: Uses `gdctl set --transform ...` to rotate the visual display.

3. Calibration: Uses the correct LIBINPUT_CALIBRATION_MATRIX and writes a udev rule to `/etc/udev/rules.d/99-touchscreen-orientation.rules`.

4. Hot-Reload:

* Reloads udev rules (`udevadm control --reload`).
* Rebinds the Driver: Temporarily unbinds and rebinds the touchscreen kernel driver to force it to read the new calibration matrix instantly.

5. GDM Sync:

   Checks if `~/.config/monitors.xml` exists and copies it to the system-wide GDM configuration path (e.g., `/var/lib/gdm/.config/` or `/etc/xdg/` depending on GNOME version).


## 📜 License

This project is licensed under the MIT License.
