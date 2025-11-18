import subprocess
import re
import os
import sys
import shutil
import argparse
import time
from typing import Optional, Tuple

def check_dependencies():
    """Checks for Wayland session and required commands using shutil (faster)."""
    
    # 1. Check Session Type
    if os.environ.get("XDG_SESSION_TYPE") != "wayland":
        print("⚠️  WARNING: XDG_SESSION_TYPE is not 'wayland'. This script is designed for Wayland.")

    # 2. Check Commands efficiently
    required_cmds = ["gdctl", "libinput", "udevadm"]
    missing = [cmd for cmd in required_cmds if shutil.which(cmd) is None]

    if missing:
        print(f"❌ ERROR: The following required commands are missing: {', '.join(missing)}")
        print("Please install the necessary packages (e.g., libinput-tools, udev).")
        sys.exit(1)

def get_active_output_wayland() -> str:
    """Calls 'gdctl show' and parses the connector name."""
    try:
        result = subprocess.run(["gdctl", "show"], check=True, capture_output=True, text=True)
        match = re.search(r'Monitor\s+([\w-]+)\s*\(', result.stdout)
        
        if match:
            return match.group(1).strip()
        
        print("⚠️  Could not parse primary monitor. Please check connection.")
        sys.exit(1)
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to run gdctl: {e.stderr.strip()}")
        sys.exit(1)

def get_touchscreen_device_wayland() -> Tuple[str, str]:
    """
    Identifies the touchscreen device using libinput.
    Returns: (Device Name, Device Kernel Node e.g. /dev/input/eventX)
    """
    try:
        result = subprocess.run(["libinput", "list-devices"], check=True, capture_output=True, text=True)
        
        # Split into blocks for each device
        device_blocks = result.stdout.split("\n\n")
        
        for block in device_blocks:
            # Check if it is a touchscreen
            if re.search(r'Device:.*Touchscreen', block, re.IGNORECASE) or "Capacity: touch" in block:
                
                # Extract Name
                name_match = re.search(r'Device:\s+(.+)', block)
                # Extract Kernel Node
                kernel_match = re.search(r'Kernel:\s+(.+)', block)
                
                if name_match and kernel_match:
                    name = name_match.group(1).strip()
                    node = kernel_match.group(1).strip()
                    return name, node

        print("❌ No touchscreen device found via libinput.")
        sys.exit(1)

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to list devices: {e}")
        sys.exit(1)

def get_calibration_matrix(choice: int) -> Tuple[Optional[str], Optional[str]]:
    """Returns (gdctl_transform, libinput_matrix)."""
    mapping = {
        1: ("normal", "1 0 0 0 1 0"),       # Landscape
        2: ("270", "0 1 0 -1 0 1"),         # Portrait (Right-side up)
        3: ("90", "0 -1 1 1 0 0"),          # Portrait (Left-side up)
        4: ("180", "-1 0 1 0 -1 1")         # Inverted
    }
    return mapping.get(choice, (None, None))

def get_gnome_major_version() -> int:
    """Returns the major GNOME shell version (e.g., 45, 48, 49). Returns 0 if detection fails."""
    try:
        res = subprocess.run(["gnome-shell", "--version"], check=True, capture_output=True, text=True)
        # Output example: "GNOME Shell 46.0" or "GNOME Shell 49.rc"
        match = re.search(r'GNOME Shell\s+(\d+)', res.stdout)
        if match:
            return int(match.group(1))
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        pass
    return 0

def force_device_rebind(device_node: str):
    """
    Forces a driver unbind/bind for the specific device to reload udev properties instantly.
    This simulates a physical unplug/replug.
    """
    print(f"⚡ Attempting to restart driver for {device_node}...")

    try:
        # 1. Find the sysfs path using udevadm
        # Returns something like: /devices/pci0000:00/.../i2c-1/1-0010/input/input18/event18
        sys_rel_path = subprocess.check_output(
            ["udevadm", "info", "-q", "path", "-n", device_node]
        ).decode().strip()
        
        sys_full_path = f"/sys{sys_rel_path}"
        
        # 2. Walk up the tree to find the device that has a 'driver' link.
        # We start at the event node and go up until we find the actual hardware device (USB/I2C/HID)
        candidate_path = sys_full_path
        driver_real_path = None
        device_id = None

        # Safety limit for walking up
        for _ in range(5):
            driver_link = os.path.join(candidate_path, "driver")
            if os.path.exists(driver_link):
                # CRITICAL FIX: Resolve the absolute path to the driver NOW.
                # The 'driver' symlink inside the device folder disappears 
                # the moment we unbind the device!
                driver_real_path = os.path.realpath(driver_link)
                device_id = os.path.basename(candidate_path)
                break
            candidate_path = os.path.dirname(candidate_path)
        
        if not driver_real_path or not device_id:
            print("⚠️  Could not find driver path in sysfs. Falling back to simple udev trigger.")
            subprocess.run(["sudo", "udevadm", "trigger", "--action=add", "--subsystem-match=input"], check=True)
            return

        print(f"   Target Hardware Device: {device_id}")
        print(f"   Driver Path: {driver_real_path}")
        
        bind_path = os.path.join(driver_real_path, "bind")
        unbind_path = os.path.join(driver_real_path, "unbind")
        
        # 3. Perform the Reset (Unbind -> Wait -> Bind)
        # We use shell redirection because writing to sysfs requires root
        unbind_cmd = f"echo '{device_id}' | sudo tee {unbind_path}"
        bind_cmd = f"echo '{device_id}' | sudo tee {bind_path}"
        
        # Ignore errors on unbind (in case it's already weird), but check bind
        subprocess.run(unbind_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.0) # Give kernel a moment to breathe
        subprocess.run(bind_cmd, shell=True, check=True, stdout=subprocess.DEVNULL)
        
        print("✅ Driver successfully restarted. Calibration should be active.")
        return True

    except Exception as e:
        print(f"❌ Failed to rebind driver: {e}")
        print("   Running fallback trigger...")
        subprocess.run(["sudo", "udevadm", "trigger", "--action=add", "--subsystem-match=input"])
        return False

def apply_gdm_configuration():
    """Detects GDM path and offers to copy monitors.xml for the login screen."""
    print('\n🔐 **GDM LOGIN SCREEN CONFIGURATION**')
    
    source_xml = os.path.expanduser("~/.config/monitors.xml")
    if not os.path.exists(source_xml):
        print("⚠️  Could not find ~/.config/monitors.xml. Cannot apply settings to login screen automatically.")
        return

    gnome_ver = get_gnome_major_version()
    if gnome_ver > 0:
        print(f"   Detected GNOME Shell Version: {gnome_ver}")

    # Determine potential GDM home directories
    targets = []
    
    # GNOME 49+ prefers /etc/xdg/monitors.xml
    if gnome_ver >= 49:
        print("   GNOME 49+ detected: Using system-wide XDG configuration.")
        targets.append("/etc/xdg/monitors.xml")
    else:
        # Legacy / Standard GDM paths (GNOME <= 48)
        # Arch / Fedora / Standard
        if os.path.isdir("/var/lib/gdm/.config"):
            targets.append("/var/lib/gdm/.config/monitors.xml")
        # Debian / Ubuntu
        if os.path.isdir("/var/lib/gdm3/.config"):
            targets.append("/var/lib/gdm3/.config/monitors.xml")
        
        # Fallback if standard GDM paths are missing
        if not targets and os.path.isdir("/etc/xdg"):
             targets.append("/etc/xdg/monitors.xml")

    if not targets:
        print("⚠️  Could not detect GDM configuration directory.")
        return

    print(f"   Found monitor config at: {source_xml}")
    print(f"   Target(s): {', '.join(targets)}")
    
    choice = input("   Do you want to apply rotation to the login screen? (y/n): ").lower().strip()
    if choice != 'y':
        print("   Skipping GDM configuration.")
        return

    for target in targets:
        try:
            print(f"   Copying to {target}...")
            # Using sudo cp
            subprocess.run(["sudo", "cp", source_xml, target], check=True)
            # Correct ownership is crucial. Usually root:gdm or root:root depending on distro, 
            # but the file MUST be readable by the gdm user.
            # We set it to root:root but readable by all (644).
            subprocess.run(["sudo", "chmod", "644", target], check=True)
            subprocess.run(["sudo", "chown", "root:root", target], check=True) # Safe default
            print(f"   ✅ Successfully updated {target}")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to copy to {target}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Touchscreen Rotation & Calibration for GNOME/Wayland")
    parser.add_argument("-o", "--orientation", type=int, choices=[1, 2, 3, 4], help="1:Normal, 2:Right, 3:Left, 4:Inverted")
    parser.add_argument("--skip-reboot", action="store_true", help="Skip the reboot prompt")
    parser.add_argument("--skip-gdm", action="store_true", help="Skip GDM configuration prompt")
    args = parser.parse_args()

    check_dependencies()
    
    print("🔍 Detecting Hardware...")
    monitor = get_active_output_wayland()
    touch_name, touch_node = get_touchscreen_device_wayland()
    
    print(f"   Display: {monitor}")
    print(f"   Touch:   {touch_name}")
    print(f"   Node:    {touch_node}")
    print("-" * 40)

    # Selection Logic
    choice = args.orientation
    if choice is None:
        print("Select screen orientation:")
        print("1) Landscape (normal)")
        print("2) Portrait (right side up)")
        print("3) Portrait (left side up)")
        print("4) Inverted (upside down)")
        try:
            c = input("Enter your choice (1-4): ")
            choice = int(c)
        except ValueError:
            print("❌ Invalid input.")
            sys.exit(1)

    transform, matrix = get_calibration_matrix(choice)
    if not transform:
        print("❌ Invalid choice.")
        sys.exit(1)

    # 1. Apply Display Rotation (gdctl)
    print(f"\n⚙️  Applying Display Rotation ({transform})...")
    try:
        cmd = [
            "gdctl", "set", "--persistent",
            "--logical-monitor", "--monitor", monitor,
            "--primary", "--transform", transform
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        print("✅ Display rotated.")
    except subprocess.CalledProcessError as e:
        print(f"❌ gdctl error: {e.stderr.decode().strip() if e.stderr else 'Unknown error'}")
        return

    # 2. Apply Touch Calibration (udev)
    print("\n📝 Writing udev rule...")
    rule_content = f'ATTRS{{name}}=="{touch_name}", ENV{{LIBINPUT_CALIBRATION_MATRIX}}="{matrix}"'
    rule_path = "/etc/udev/rules.d/99-touchscreen-orientation.rules"
    
    try:
        ps = subprocess.Popen(["echo", rule_content], stdout=subprocess.PIPE)
        subprocess.check_output(["sudo", "tee", rule_path], stdin=ps.stdout)
        ps.wait()
        print("✅ udev rule written.")
    except subprocess.CalledProcessError:
        print("❌ Failed to write udev rule. Sudo failed.")
        return

    # 3. Apply Changes Forcefully
    print("\n🔄 Reloading Configuration...")
    subprocess.run(["sudo", "udevadm", "control", "--reload-rules"], check=True)
    
    # Use the heavy hammer: Rebind the driver
    success = force_device_rebind(touch_node)

    # 4. GDM Configuration (New)
    if not args.skip_gdm:
        apply_gdm_configuration()

    if not success and not args.skip_reboot:
        print("\n⚠️  Hot-reload failed. A reboot is required.")
        if input("Reboot now? (y/n): ").lower().strip() == 'y':
            subprocess.run(["sudo", "reboot"])

if __name__ == "__main__":
    main()
