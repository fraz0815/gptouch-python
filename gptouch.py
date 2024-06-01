import subprocess
import re
import os

def check_command(command, name):
    try:
        subprocess.run([command, "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        print(f"{name} is not installed. Please install {name} to use this feature.")
        exit(1)
    except FileNotFoundError:
        print(f"{name} command not found. Please ensure {name} is installed and in your PATH.")
        exit(1)

def check_dependencies():
    if os.environ.get("XDG_SESSION_TYPE") == "x11":
        check_command("xrandr", "xrandr")
        check_command("xinput", "xinput")
    else:
        check_command("gnome-randr", "gnome-randr")
        check_command("libinput", "libinput")

def get_active_output_x11():
    try:
        result = subprocess.run(["xrandr"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode()
        matches = re.findall(r'(\w+)\sconnected', output)
        if matches:
            return matches[0]
        else:
            print("No active output found. Please check your display connections.")
            exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Failed to get active output: {str(e)}")
        exit(1)

def get_active_output_wayland():
    try:
        result = subprocess.run(["gnome-randr"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode()
        associated_monitors = re.search(r'associated physical monitors:\n\t(\S+)', output)
        if associated_monitors:
            return associated_monitors.group(1)
        else:
            print("No active output found. Please check your display connections.")
            exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Failed to get active output: {str(e)}")
        exit(1)

def get_active_output():
    if os.environ.get("XDG_SESSION_TYPE") == "x11":
        return get_active_output_x11()
    else:
        return get_active_output_wayland()

def get_touchscreen_device_x11():
    try:
        result = subprocess.run(["xinput", "--list"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode()
        matches = re.findall(r'↳ (.*Touchscreen.*)id=\d+', output)
        if matches:
            return matches[0]
        else:
            print("No touchscreen device found. Please check your connections.")
            exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Failed to get touchscreen device: {str(e)}")
        exit(1)

def get_touchscreen_device_wayland():
    try:
        result = subprocess.run(["libinput", "list-devices"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode()
        matches = re.findall(r'Device:.*Touchscreen', output, re.IGNORECASE)
        if matches:
            return matches[0].split(":")[1].strip()
        else:
            print("No touchscreen device found. Please check your connections.")
            exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Failed to get touchscreen device: {str(e)}")
        exit(1)

def get_touchscreen_device():
    if os.environ.get("XDG_SESSION_TYPE") == "x11":
        return get_touchscreen_device_x11()
    else:
        return get_touchscreen_device_wayland()

def select_orientation():
    print("Select screen orientation:")
    print("1) Landscape (normal)")
    print("2) Portrait (right side up)")
    print("3) Portrait (left side up)")
    print("4) Inverted (upside down)")
    choice = input("Enter your choice (1-4): ")
    return int(choice)

def update_calibration_matrix(choice):
    calibration_matrices = {
        1: ("normal", "1 0 0 0 1 0"),
        2: ("left", "0 1 0 -1 0 1"),
        3: ("right", "0 -1 1 1 0 0"),
        4: ("inverted", "-1 0 1 0 -1 1")
    }
    return calibration_matrices.get(choice, (None, None))

def main():
    check_dependencies()
    OUTPUT_DISPLAY_DEFAULT = get_active_output()
    TOUCHSCREEN_DEVICE_DEFAULT = get_touchscreen_device()
    
    choice = select_orientation()
    if choice not in [1, 2, 3, 4]:
        print("Invalid choice. Exiting...")
        return

    rotation, calibration_matrix = update_calibration_matrix(choice)
    if not rotation:
        print("Invalid choice. Exiting...")
        return

    if os.environ.get("XDG_SESSION_TYPE") == "x11":
        # Rotate the display using xrandr
        subprocess.run(["xrandr", "--output", OUTPUT_DISPLAY_DEFAULT, "--rotate", rotation])
    else:
        # Rotate the display using gnome-randr
        subprocess.run(["gnome-randr", "modify", OUTPUT_DISPLAY_DEFAULT, "--rotate", rotation, "--persistent"])
    
    print()
    subprocess.run(["sudo", "tee", "/etc/udev/rules.d/99-touchscreen-orientation.rules"], input=f'ATTRS{{name}}=="{TOUCHSCREEN_DEVICE_DEFAULT}", ENV{{LIBINPUT_CALIBRATION_MATRIX}}="{calibration_matrix}"'.encode())

    print()
    reboot = input("Reboot now? (y/n): ").strip().lower()
    if reboot == 'y':
        subprocess.run(["sudo", "reboot"])
    else:
        print("Reboot cancelled. Changes will apply on next reboot.")

if __name__ == "__main__":
    main()
