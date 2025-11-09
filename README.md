## 🖥️ Touchscreen Rotation and Calibration Script for GNOME (Wayland)

This Python script offers a terminal interface to automatically rotate the display and calibrate the touchscreen input matrix in **Wayland environments**. It uses the modern **`gdctl`** utility (GNOME $\geq 48$) for persistent display configuration and `libinput` for the touchscreen matrix.

-----

## 🛠️ Requirements

The script is strictly intended for use under **Wayland** (GNOME).

### 🛑 Required Dependencies

  * **Python 3**
  * **`gdctl`** (Part of GNOME; for persistent display rotation)
  * **`libinput`** (for Wayland input management and calibration)
  * The user must be in the **`input` group** (see Installation).
  * `sudo` permissions for writing udev rules.

### 💡 Optional Dependency

  * **`gdm-settings`**: A tool to apply the display settings (rotation) set by `gdctl` to the **GDM (GNOME Display Manager) login screen**. The script checks for its presence and provides a specific hint.

-----

## 📥 Installation

### 1\. Install Dependencies

#### Debian-based Distributions

```bash
# Required packages
sudo apt-get install python3 libinput-tools

# Optional dependency (installation method may vary)
# Install gdm-settings if desired.
```

#### Arch-based Distributions

```bash
# Required packages
sudo pacman -S python libinput

# Optional dependency
# gdm-settings can typically be installed via the AUR (e.g., using yay).
# yay -S gdm-settings 
```

### 2\. Add User to the `input` Group

To execute `libinput` operations without needing `sudo`, add your user to the `input` group. 

**A re-login is required.**

```bash
sudo usermod -a -G input YOUR_USERNAME
```

-----

## 💡 Usage

Run the script using Python:

```bash
python3 gptouch.py
```

### Orientation Options

The script will prompt you to choose one of the following orientations. The display rotation and touchscreen calibration matrix will be set simultaneously.

1.  **Landscape** (`normal`)
2.  **Portrait** (`right` side up)
3.  **Portrait** (`left` side up)
4.  **Inverted** (`upside down`)

### Script Flow Highlights

1.  Checks for required and optional dependencies (`gdctl`, `libinput`, `gdm-settings`).
2.  Determines the active display connector name (e.g., `HDMI-1`) via **`gdctl show`**.
3.  Applies the rotation using `gdctl set --persistent --primary --transform [ANGLE]`, ensuring **desktop rotation is saved permanently.**
4.  Writes the corresponding calibration matrix to the udev rules file (`/etc/udev/rules.d/...`).
5.  A **specific hint** is provided:
      * If `gdm-settings` is installed, the user is reminded to use it to set the rotation on the **GDM login screen** (which is separate from the desktop session).
6.  Prompts for a reboot to apply the new udev rules.

-----

## 📜 License

This project is licensed under the MIT License.
