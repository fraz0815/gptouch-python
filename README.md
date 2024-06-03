# Touchscreen Rotation and Calibration Matrix Script for Gnome

This script provides a terminal interface to rotate the display and calibrate the touchscreen input matrix on both Wayland and X11 (experimental/broken, see Troubleshooting) environments automatically.

## Requirements

- Python 3
- `xrandr` and `xinput` (for X11)
- [`gnome-randr`](https://github.com/maxwellainatchi/gnome-randr-rust) and `libinput` (for Wayland)
- `sudo` privileges for modifying udev rules
- optional [`gdm-settings`](https://github.com/gdm-settings/gdm-settings) for login screen

## Installation

### Debian-based Distributions

1. **Install Python**:
    ```bash
    sudo apt-get install python3
    ```

2. **Install X11 Dependencies** (if using X11):
    ```bash
    sudo apt-get install x11-xserver-utils xinput
    ```

3. **Install Wayland Dependencies** (if using Wayland):
    ```bash
    sudo apt-get install libinput-tools
    ```

4. **Install `gnome-randr`**:
    - `gnome-randr` can be installed using Cargo, the Rust package manager. First, ensure you have Rust and Cargo installed. Follow the instructions at [rust-lang.org](https://www.rust-lang.org/tools/install).
    - Once Rust and Cargo are installed, you can install `gnome-randr` by running:
      ```bash
      cargo install gnome-randr
      ```

### Arch-based Distributions

1. **Install Python**:
    ```bash
    sudo pacman -S python
    ```

2. **Install X11 Dependencies** (if using X11):
    ```bash
    sudo pacman -S xorg-xrandr xorg-xinput
    ```

3. **Install Wayland Dependencies** (if using Wayland):
    ```bash
    sudo pacman -S libinput
    ```

4. **Install `gnome-randr`**:
    - `gnome-randr` can be installed using Cargo, the Rust package manager. First, ensure you have Rust and Cargo installed. Follow the instructions at [rust-lang.org](https://www.rust-lang.org/tools/install).
    - Once Rust and Cargo are installed, you can install `gnome-randr` by running:
      ```bash
      cargo install gnome-randr
      ```

## Usage

Run the script using Python:
```bash
python3 gptouch.py
```

### Script Flow

1. The script checks for the required dependencies (`xrandr`, `xinput`, `gnome-randr`, and `libinput`).
2. It determines the active display output based on the session type (`X11` or Wayland).
3. It identifies the connected touchscreen device.
4. It prompts the user to select the desired screen orientation.
5. It applies the selected screen orientation.
6. It updates the touchscreen calibration matrix and writes it to the udev rules, using `sudo`.
7. It prompts the user to reboot the system to apply the changes.

### Orientation Options

- 1: Landscape (normal)
- 2: Portrait (right side up)
- 3: Portrait (left side up)
- 4: Inverted (upside down)

## Notes

- The script requires `sudo` privileges to modify udev rules.
- Users should be in the `input` group to avoid needing `sudo` for these operations.
- Use [`gdm-settings`](https://github.com/gdm-settings/gdm-settings) to apply rotation on login screen

### Troubleshooting

- **Dependency Errors**: Ensure all required packages are installed.
- **Display Not Found**: Verify that your display is correctly connected and detected by the system.
- **Touchscreen Device Not Found**: Check the connections and ensure the device is recognized by the system.
- **X11**: xrandr and gnome-randr handle left/right different, also xrandr needs storing - use [`arandr`](https://christian.amsuess.com/tools/arandr/)

## License

This project is licensed under the MIT License.

## Acknowledgements

- `xrandr` and `xinput` are used for X11 display and input management.
- [`gnome-randr`](https://github.com/maxwellainatchi/gnome-randr-rust) and `libinput` are used for Wayland display and input management.
