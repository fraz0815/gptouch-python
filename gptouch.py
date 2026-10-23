import subprocess
import re
import os
import sys
import shutil
import argparse
import time
from typing import Optional, Tuple

# Erzwinge englische Ausgaben fuer zuverlaessiges Regex-Parsing
SUBPROCESS_ENV = {**os.environ, "LC_ALL": "C"}

def check_dependencies():
    """Checks for Wayland session and required commands using shutil (faster)."""
    if os.environ.get("XDG_SESSION_TYPE") != "wayland":
        print("[WARN] XDG_SESSION_TYPE is not 'wayland'. This script is designed for Wayland.")

    required_cmds = ["gdctl", "libinput", "udevadm"]
    missing = [cmd for cmd in required_cmds if shutil.which(cmd) is None]

    if missing:
        print(f"[ERROR] The following required commands are missing: {', '.join(missing)}")
        print("Please install the necessary packages (e.g., libinput-tools, udev).")
        sys.exit(1)

def get_active_output_wayland() -> Tuple[str, Optional[str]]:
    """
    Calls 'gdctl show' and parses the active connector name and its current scale.
    Returns: (connector_name, scale_str)
    """
    try:
        result = subprocess.run(
            ["gdctl", "show"],
            check=True,
            capture_output=True,
            text=True,
            env=SUBPROCESS_ENV
        )
        output = result.stdout

        # Bevorzugt in 'Logical monitors:' suchen, um nur aktive Screens + deren Skalierung zu erwischen
        logical_section = output.split("Logical monitors:")[-1] if "Logical monitors:" in output else output

        monitor_match = re.search(r'Monitor\s+([\w-]+)\s*\(', logical_section)
        if not monitor_match:
            monitor_match = re.search(r'Monitor\s+([\w-]+)\s*\(', output)

        scale_match = re.search(r'Scale:\s+([\d.]+)', logical_section)
        scale = scale_match.group(1).strip() if scale_match else None

        if monitor_match:
            return monitor_match.group(1).strip(), scale

        print("[ERROR] Could not parse primary monitor. Please check connection.")
        sys.exit(1)

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to run gdctl: {e.stderr.strip()}")
        sys.exit(1)

def get_touchscreen_device_wayland() -> Tuple[str, str]:
    """
    Identifies the touchscreen device using libinput.
    Returns: (Device Name, Device Kernel Node e.g. /dev/input/eventX)
    """
    try:
        result = subprocess.run(
            ["libinput", "list-devices"],
            check=True,
            capture_output=True,
            text=True,
            env=SUBPROCESS_ENV
        )

        device_blocks = result.stdout.strip().split("\n\n")

        for block in device_blocks:
            cap_match = re.search(r'Capabilities:\s+(.*)', block)
            if cap_match:
                capabilities = cap_match.group(1).lower().split()

                if "touch" in capabilities:
                    name_match = re.search(r'Device:\s+(.+)', block)
                    kernel_match = re.search(r'Kernel:\s+(.+)', block)

                    if name_match and kernel_match:
                        name = name_match.group(1).strip()
                        node = kernel_match.group(1).strip()
                        if "touchpad" in name.lower():
                            continue
                        return name, node

        print("[ERROR] No touchscreen device found via libinput.")
        sys.exit(1)

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to list devices: {e}")
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
    """Returns the major GNOME shell version (e.g., 48, 49, 50, 51). Returns 0 if detection fails."""
    try:
        res = subprocess.run(
            ["gnome-shell", "--version"],
            check=True,
            capture_output=True,
            text=True,
            env=SUBPROCESS_ENV
        )
        match = re.search(r'GNOME Shell\s+(\d+)', res.stdout)
        if match:
            return int(match.group(1))
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        pass
    return 0

def force_device_rebind(device_node: str) -> bool:
    """
    Forces a driver unbind/bind for the specific device to reload udev properties instantly.
    This simulates a physical unplug/replug.
    """
    print(f"[INFO] Attempting to restart driver for {device_node}...")

    try:
        sys_rel_path = subprocess.check_output(
            ["udevadm", "info", "-q", "path", "-n", device_node],
            env=SUBPROCESS_ENV,
            text=True
        ).strip()

        sys_full_path = f"/sys{sys_rel_path}"

        candidate_path = sys_full_path
        driver_real_path = None
        device_id = None

        for _ in range(5):
            driver_link = os.path.join(candidate_path, "driver")
            if os.path.exists(driver_link):
                driver_real_path = os.path.realpath(driver_link)
                device_id = os.path.basename(candidate_path)
                break
            candidate_path = os.path.dirname(candidate_path)

        if not driver_real_path or not device_id:
            print("[WARN] Could not find driver path in sysfs. Falling back to udev trigger.")
            subprocess.run(["sudo", "udevadm", "trigger", "--action=change", device_node], check=True)
            return True

        print(f"       Target Hardware Device: {device_id}")
        print(f"       Driver Path: {driver_real_path}")

        bind_path = os.path.join(driver_real_path, "bind")
        unbind_path = os.path.join(driver_real_path, "unbind")

        # Sauberes Schreiben via stdin ohne shell=True
        subprocess.run(
            ["sudo", "tee", unbind_path],
            input=device_id,
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(1.0)
        subprocess.run(
            ["sudo", "tee", bind_path],
            input=device_id,
            text=True,
            check=True,
            stdout=subprocess.DEVNULL
        )

        print("[OK] Driver successfully restarted. Calibration is active.")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to rebind driver: {e}")
        print("        Running fallback trigger...")
        subprocess.run(["sudo", "udevadm", "trigger", "--action=change", "--subsystem-match=input"])
        return False

def apply_gdm_configuration():
    """Detects GDM path and offers to copy monitors.xml for the login screen."""
    print("\n--- GDM LOGIN SCREEN CONFIGURATION ---")

    source_xml = os.path.expanduser("~/.config/monitors.xml")
    if not os.path.exists(source_xml):
        print("[WARN] Could not find ~/.config/monitors.xml. Cannot apply settings to login screen automatically.")
        return

    gnome_ver = get_gnome_major_version()
    if gnome_ver > 0:
        print(f"[INFO] Detected GNOME Shell Version: {gnome_ver}")

    targets = []

    # GNOME 49, 50, 51+ nutzen bevorzugt /etc/xdg/monitors.xml
    if gnome_ver >= 49:
        print(f"[INFO] GNOME {gnome_ver} detected: Using system-wide XDG configuration.")
        targets.append("/etc/xdg/monitors.xml")
    else:
        if os.path.isdir("/var/lib/gdm/.config"):
            targets.append("/var/lib/gdm/.config/monitors.xml")
        if os.path.isdir("/var/lib/gdm3/.config"):
            targets.append("/var/lib/gdm3/.config/monitors.xml")
        if not targets and os.path.isdir("/etc/xdg"):
            targets.append("/etc/xdg/monitors.xml")

    if not targets:
        print("[WARN] Could not detect GDM configuration directory.")
        return

    print(f"       Found monitor config at: {source_xml}")
    print(f"       Target(s): {', '.join(targets)}")

    choice = input("Do you want to apply rotation to the login screen? (y/n): ").lower().strip()
    if choice != 'y':
        print("[INFO] Skipping GDM configuration.")
        return

    for target in targets:
        try:
            print(f"[INFO] Copying to {target}...")
            subprocess.run(["sudo", "cp", source_xml, target], check=True)
            subprocess.run(["sudo", "chmod", "644", target], check=True)
            subprocess.run(["sudo", "chown", "root:root", target], check=True)
            print(f"[OK] Successfully updated {target}")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to copy to {target}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Touchscreen Rotation & Calibration for GNOME/Wayland")
    parser.add_argument("-o", "--orientation", type=int, choices=[1, 2, 3, 4], help="1:Normal, 2:Right, 3:Left, 4:Inverted")
    parser.add_argument("--skip-reboot", action="store_true", help="Skip the reboot prompt")
    parser.add_argument("--skip-gdm", action="store_true", help="Skip GDM configuration prompt")
    args = parser.parse_args()

    check_dependencies()

    print("[INFO] Detecting hardware...")
    monitor, current_scale = get_active_output_wayland()
    touch_name, touch_node = get_touchscreen_device_wayland()

    print(f"       Display: {monitor} (Scale: {current_scale or 'default'})")
    print(f"       Touch:   {touch_name}")
    print(f"       Node:    {touch_node}")
    print("-" * 40)

    choice = args.orientation
    if choice is None:
        print("Select screen orientation:")
        print("  1) Landscape (normal)")
        print("  2) Portrait (right side up)")
        print("  3) Portrait (left side up)")
        print("  4) Inverted (upside down)")
        try:
            c = input("Enter your choice (1-4): ")
            choice = int(c)
        except ValueError:
            print("[ERROR] Invalid input.")
            sys.exit(1)

    transform, matrix = get_calibration_matrix(choice)
    if not transform:
        print("[ERROR] Invalid choice.")
        sys.exit(1)

    # 1. Apply Display Rotation (gdctl)
    print(f"\n[INFO] Applying display rotation ({transform})...")
    try:
        cmd = [
            "gdctl", "set", "--persistent",
            "--logical-monitor", "--monitor", monitor,
            "--primary", "--transform", transform
        ]
        # Aktuelle Skalierung beibehalten, falls vorhanden
        if current_scale:
            cmd.extend(["--scale", current_scale])

        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("[OK] Display rotated.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] gdctl error: {e.stderr.strip() if e.stderr else 'Unknown error'}")
        return

    # 2. Apply Touch Calibration (udev)
    print("[INFO] Writing udev rule...")
    rule_content = f'ATTRS{{name}}=="{touch_name}", ENV{{LIBINPUT_CALIBRATION_MATRIX}}="{matrix}"\n'
    rule_path = "/etc/udev/rules.d/99-touchscreen-orientation.rules"

    try:
        subprocess.run(
            ["sudo", "tee", rule_path],
            input=rule_content,
            text=True,
            check=True,
            stdout=subprocess.DEVNULL
        )
        print("[OK] udev rule written.")
    except subprocess.CalledProcessError:
        print("[ERROR] Failed to write udev rule. Sudo failed.")
        return

    # 3. Apply Changes Forcefully
    print("[INFO] Reloading configuration...")
    subprocess.run(["sudo", "udevadm", "control", "--reload-rules"], check=True)

    success = force_device_rebind(touch_node)

    # 4. GDM Configuration
    if not args.skip_gdm:
        apply_gdm_configuration()

    if not success and not args.skip_reboot:
        print("\n[WARN] Hot-reload failed. A reboot is required.")
        if input("Reboot now? (y/n): ").lower().strip() == 'y':
            subprocess.run(["sudo", "reboot"])

if __name__ == "__main__":
    main()
