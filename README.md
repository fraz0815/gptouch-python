That's a very helpful distinction to make\! It's better to manage user expectations upfront, as integrated touchscreen laptops often handle rotation automatically via internal sensors.

I will add a clear clarifying statement right at the beginning of the `README.md`.

-----

# fraz0815/gptouch-python

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
| **Arch/Fedora** | `sudo pacman -S python libinput` |

### 2\. Add User to the `input` Group

To execute `libinput` operations without needing `sudo`, add your user to the `input` group. **A re-login is required.**

| Distribution Type | Command |
| :--- | :--- |
| **Debian/Ubuntu** | `sudo usermod -a -G input YOUR_USERNAME` |
| **Arch/Fedora** | `sudo usermod -aG input YOUR_USERNAME` |

-----

## 💡 Usage

Run the script using Python:

```bash
python3 gptouch.py
```

### Orientation Options

The script will prompt you to choose one of the following orientations. Both the display rotation (`gdctl`) and the touchscreen calibration matrix will be set simultaneously and persistently.

1.  **Landscape** (`normal`)
2.  **Portrait** (`right` side up)
3.  **Portrait** (`left` side up)
4.  **Inverted** (`upside down`)

### Script Flow Highlights

1.  Checks for required dependencies (`gdctl`, `libinput`).
2.  Determines the active display connector name (e.g., `HDMI-1`) via **`gdctl show`**.
3.  Applies the rotation using `gdctl set --persistent --primary --transform [ANGLE]`, ensuring **desktop rotation is saved permanently.**
4.  Writes the corresponding calibration matrix to the udev rules file (`/etc/udev/rules.d/...`).
5.  Provides instructions for updating the GDM login screen configuration.
6.  Prompts for a reboot to apply the new udev rules.

-----

## 🔒 GDM Login Screen Rotation (Optional Step)

The rotation set by `gdctl set --persistent` saves the configuration for your **user session**. The **GDM login screen** uses a separate configuration file (`monitors.xml`). If the login screen is not rotated after applying the script, use the following steps to update GDM's configuration file.

After the script completes, you must manually copy your session's configuration file to the GDM path to ensure the login screen matches your desktop rotation. **Choose only the path that applies to your system:**

| GNOME Version | Distribution Type | Command |
| :--- | :--- | :--- |
| **GNOME 49+** (Recommended) | Cross-Distro Standard | `sudo cp ~/.config/monitors.xml /etc/xdg/monitors.xml && sudo chmod 644 /etc/xdg/monitors.xml` |
| **GNOME 48** | Arch/Fedora-like | `sudo cp ~/.config/monitors.xml /var/lib/gdm/.config/monitors.xml` |
| **GNOME 48** | Debian/Ubuntu-like | `sudo cp ~/.config/monitors.xml /var/lib/gdm3/.config/monitors.xml` |

-----

## 📜 License

This project is licensed under the MIT License.
