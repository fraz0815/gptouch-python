import subprocess
import re
import os
import sys

def check_command(command, name, is_optional=False):
    """Checks if a command exists and is executable."""
    try:
        # Check by running with --help (since gdctl doesn't have --version)
        subprocess.run([command, "--help"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        if not is_optional:
            print(f"**ERROR:** {name} is installed but failed to execute. Please check the installation.")
            sys.exit(1)
        return False
    except FileNotFoundError:
        if not is_optional:
            print(f"**ERROR:** {name} command not found. Please ensure {name} is installed and in your PATH.")
            sys.exit(1)
        return False

def check_dependencies():
    """Checks for Wayland session and required commands (gdctl, libinput) and optional gdm-settings."""
    
    if os.environ.get("XDG_SESSION_TYPE") == "x11":
         print("X11 is not supported. This script is intended for Wayland only.")
         sys.exit(1)
    
    # Required dependencies
    check_command("gdctl", "gdctl", is_optional=False)
    check_command("libinput", "libinput", is_optional=False)
    
    # OPTIONAL dependency
    if check_command("gdm-settings", "gdm-settings", is_optional=True):
        print("✅ gdm-settings found. You can use it to apply rotation to GDM.")
        return True # gdm-settings is installed
    else:
        print("⚠️ gdm-settings NOT found. Rotation will only apply to your current session.")
        print("   (The udev rule for the touchscreen will still work after reboot.)")
        return False # gdm-settings is missing

def get_active_output_wayland():
    """Calls 'gdctl show' and parses the name of the active display output (Connector name)."""
    try:
        # Use 'show' command
        result = subprocess.run(["gdctl", "show"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output = result.stdout
        
        # Regex: Find the connector name (e.g., HDMI-1) by looking for 'Monitor' followed by the name, then '('.
        match = re.search(r'Monitor\s*([A-Z0-9-]+)\s*\(', output) 
        
        if match:
            # The connector name is in the first capturing group
            return match.group(1).strip()
        else:
            print("No active output found. Could not parse monitor name from 'gdctl show' output.")
            print("Please ensure your display is connected and active.")
            sys.exit(1)
            
    except subprocess.CalledProcessError as e:
        print(f"Failed to get active output using gdctl: {e.stderr.strip()}")
        sys.exit(1)
    except FileNotFoundError:
        print("gdctl command not found. Please ensure gdctl is installed.")
        sys.exit(1)


def get_touchscreen_device_wayland():
    """Identifies the touchscreen device using libinput."""
    try:
        result = subprocess.run(["libinput", "list-devices"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode()
        matches = re.findall(r'Device:.*Touchscreen', output, re.IGNORECASE)
        if matches:
            return matches[0].split(":")[1].strip()
        else:
            print("No touchscreen device found. Please check your connections.")
            print("Also, ensure the user is in the 'input' group (see Readme).")
            sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Failed to get touchscreen device: {str(e)}")
        sys.exit(1)

def select_orientation():
    """Prompts the user for the desired orientation."""
    print("Select screen orientation:")
    print("1) Landscape (normal)")
    print("2) Portrait (right side up)")
    print("3) Portrait (left side up)")
    print("4) Inverted (upside down)")
    choice = input("Enter your choice (1-4): ")
    return int(choice)

def get_calibration_matrix(choice):
    """Returns the gdctl transform parameter and the libinput calibration matrix."""
    
    # FINAL CORRECTION: Transforms and Matrices for 2 and 3 are swapped as gnome-randr and gdctl use a different logic.
    calibration_matrices = {
        # gdctl-Transform, libinput-Matrix
        1: ("normal", "1 0 0 0 1 0"),      # Landscape
        2: ("270", "0 1 0 -1 0 1"),	 # Portrait (right side up) - now uses 270 transform and left matrix
        3: ("90", "0 -1 1 1 0 0"),       # Portrait (left side up) - now uses 90 transform and right matrix
        4: ("180", "-1 0 1 0 -1 1")       # Inverted
    }
    return calibration_matrices.get(choice, (None, None))

def main():
    GDM_SETTINGS_INSTALLED = check_dependencies()
    
    OUTPUT_DISPLAY_DEFAULT = get_active_output_wayland()
    TOUCHSCREEN_DEVICE_DEFAULT = get_touchscreen_device_wayland()
    
    try:
        choice = select_orientation()
    except ValueError:
        print("Invalid input. Exiting...")
        return
        
    if choice not in [1, 2, 3, 4]:
        print("Invalid choice. Exiting...")
        return
  
    # transform will be 'normal', '90', '180', or '270'
    transform, calibration_matrix = get_calibration_matrix(choice)
    if not transform:
        print("Invalid choice. Exiting...")
        return

    # Apply rotation using 'gdctl set' with --persistent and --primary
    try:
        command = [
            "gdctl", 
            "set", 
            "--persistent", # Must be placed first (global scope)
            "--logical-monitor", 
            "--monitor", OUTPUT_DISPLAY_DEFAULT,
            "--primary", # Fixes "Config is missing primary logical" error
            "--transform", transform 
        ]
        # --persistent stores the configuration persistently
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"✅ Desktop rotation successfully set to transform '{transform}' using gdctl and stored persistently.")
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR applying rotation with gdctl.")
        print(f"Command: {' '.join(command)}")
        print(f"Error message: {e.stderr.decode().strip()}")
        print("Check permissions or potential GDM errors.")
        return
 
    # Write the Touch Calibration Matrix to udev rules
    print()
    try:
        # Use 'sudo sh -c' with 'echo' to ensure a clean file write without artifacts
        udev_rule_content = f'ATTRS{{name}}=="{TOUCHSCREEN_DEVICE_DEFAULT}", ENV{{LIBINPUT_CALIBRATION_MATRIX}}="{calibration_matrix}"'
        udev_command = [
            "sudo", 
            "sh", 
            "-c", 
            f"echo '{udev_rule_content}' > /etc/udev/rules.d/99-touchscreen-orientation.rules"
        ]

        subprocess.run(udev_command, check=True)
        print("✅ Touchscreen calibration rule successfully written to udev.")
    except subprocess.CalledProcessError as e:
        # Note: If this fails, the error message may be less descriptive due to 'sh -c'
        print(f"❌ ERROR writing udev rule. Do you have sudo permissions?")
        print(f"Error message: Check your system logs or ensure sudo is configured correctly.")
        return

    print()

    # Conditional hint with clarification
    if GDM_SETTINGS_INSTALLED:
        print('💡 **HINT:** Your **desktop** rotation is saved.')
        print('    Use gdm-settings to apply this rotation to the **GDM login screen** only.')
    else:
        print('⚠️ **HINT:** Your **desktop** rotation is saved, but gdm-settings is NOT installed.')
        print('    The rotation will NOT be applied to the **GDM login screen**. Install gdm-settings if you wish to set it.')

    print()
    reboot = input("Reboot now? (y/n): ").strip().lower()
    if reboot == 'y':
        subprocess.run(["sudo", "reboot"])
    else:
        print("Reboot cancelled. Changes will take effect on the next reboot.")

if __name__ == "__main__":
    main()
