import St from 'gi://St';
import GLib from 'gi://GLib';
import GObject from 'gi://GObject';
import { Extension } from 'resource:///org/gnome/shell/extensions/extension.js';
import * as panelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';

const GpTouchMenu = GObject.registerClass(
class GpTouchMenu extends panelMenu.Button {
    _init(scriptPath) {
        super._init(0.0, 'GpTouch');
        this.scriptPath = scriptPath;

        // Ein passendes Icon für Rotation aus dem System-Theme laden
        let icon = new St.Icon({
            icon_name: 'rotation-allowed-symbolic',
            style_class: 'system-status-icon',
        });
        this.add_child(icon);

        // Menüeinträge für die 4 Orientierungen erstellen
        this._addOrientationItem('Landscape (Normal)', 1);
        this._addOrientationItem('Portrait (Rechts)', 2);
        this._addOrientationItem('Portrait (Links)', 3);
        this._addOrientationItem('Inverted (Kopfstand)', 4);
    }

    _addOrientationItem(label, orientationValue) {
        let item = new PopupMenu.PopupMenuItem(label);
        item.connect('activate', () => {
            this._rotate(orientationValue);
        });
        this.menu.addMenuItem(item);
    }

  _rotate(orientationValue) {
        try {
            let terminalCmd = '';
            
            // GLib prüft, ob die Programme im System-Pfad existieren (kgx wird bevorzugt)
            if (GLib.find_program_in_path('kgx')) {
                // kgx nutzt '-e', um einen Befehl beim Start auszuführen
                terminalCmd = `kgx -e bash -c "python3 ${this.scriptPath} -o ${orientationValue} --skip-reboot"`;
            } else if (GLib.find_program_in_path('gnome-terminal')) {
                // gnome-terminal nutzt stattdessen '--'
                terminalCmd = `gnome-terminal -- bash -c "python3 ${this.scriptPath} -o ${orientationValue} --skip-reboot"`;
            } else {
                console.error("GpTouch Fehler: Weder kgx noch gnome-terminal wurden auf dem System gefunden!");
                return;
            }

            GLib.spawn_command_line_async(terminalCmd);
            console.log(`GpTouch Extension: Ausgeführt (inkl. GDM) -> ${terminalCmd}`);
        } catch (e) {
            console.error(`GpTouch Extension Fehler: ${e.message}`);
        }
    }
});

export default class GpTouchExtension extends Extension {
    enable() {
        // Sucht automatisch den absoluten Pfad zur gptouch.py innerhalb des Extension-Ordners
        const scriptPath = this.dir.get_child('gptouch.py').get_path(); 
        
        this._indicator = new GpTouchMenu(scriptPath);
        Main.panel.addToStatusArea(this.uuid, this._indicator);
    }

    disable() {
        if (this._indicator) {
            this._indicator.destroy();
            this._indicator = null;
        }
    }
}
