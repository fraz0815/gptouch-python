import tkinter as tk
from tkinter import simpledialog, messagebox
import subprocess
import re
import os

def check_command(command, name):
    try:
        subprocess.run([command, "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        messagebox.showerror("Error", f"{name} is not installed. Please install {name} to use this feature.")
        exit(1)
    except FileNotFoundError:
        messagebox.showerror("Error", f"{name} command not found. Please ensure {name} is installed and in your PATH.")
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
            messagebox.showerror("Error", "No active output found. Please check your display connections.")
            exit(1)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Failed to get active output: {str(e)}")
        exit(1)

def get_active_output_wayland():
    try:
        result = subprocess.run(["gnome-randr"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode()
        associated_monitors = re.search(r'associated physical monitors:\n\t(\S+)', output)
        if associated_monitors:
            return associated_monitors.group(1)
        else:
            messagebox.showerror("Error", "No active output found. Please check your display connections.")
            exit(1)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Failed to get active output: {str(e)}")
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
            messagebox.showerror("Error", "No touchscreen device found. Please check your connections.")
            exit(1)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Failed to get touchscreen device: {str(e)}")
        exit(1)

def get_touchscreen_device_wayland():
    try:
        result = subprocess.run(["libinput", "list-devices"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode()
        matches = re.findall(r'Device:.*Touchscreen', output, re.IGNORECASE)
        if matches:
            return matches[0].split(":")[1].strip()
        else:
            messagebox.showerror("Error", "No touchscreen device found. Please check your connections.")
            exit(1)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Failed to get touchscreen device: {str(e)}")
        exit(1)

def get_touchscreen_device():
    if os.environ.get("XDG_SESSION_TYPE") == "x11":
        return get_touchscreen_device_x11()
    else:
        return get_touchscreen_device_wayland()

def select_orientation():
    orientations = ["Landscape (normal)", "Portrait (right side up)", "Portrait (left side up)", "Inverted (upside down)"]
    choice = simpledialog.askinteger("Select Orientation", "1) Landscape (normal)\n2) Portrait (right side up)\n3) Portrait (left side up)\n4) Inverted (upside down)\nEnter your choice (1-4):", minvalue=1, maxvalue=4)
    return choice

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
    if not choice:
        messagebox.showerror("Error", "Invalid choice. Exiting...")
        return

    rotation, calibration_matrix = update_calibration_matrix(choice)
    if not rotation:
        messagebox.showerror("Error", "Invalid choice. Exiting...")
        return

    if os.environ.get("XDG_SESSION_TYPE") == "x11":
        # Rotate the display using xrandr
        subprocess.run(["xrandr", "--output", OUTPUT_DISPLAY_DEFAULT, "--rotate", rotation])
    else:
        # Rotate the display using gnome-randr
        subprocess.run(["gnome-randr", "modify", OUTPUT_DISPLAY_DEFAULT, "--rotate", rotation, "--persistent"])

    subprocess.run(["sudo", "tee", "/etc/udev/rules.d/99-touchscreen-orientation.rules"], input=f'ATTRS{{name}}=="{TOUCHSCREEN_DEVICE_DEFAULT}", ENV{{LIBINPUT_CALIBRATION_MATRIX}}="{calibration_matrix}"'.encode())

    if messagebox.askyesno("Reboot", "Reboot now?"):
        subprocess.run(["sudo", "reboot"])
    else:
        messagebox.showinfo("Cancelled", "Reboot cancelled. Changes will apply on next reboot.")

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the main Tkinter window
    main()
