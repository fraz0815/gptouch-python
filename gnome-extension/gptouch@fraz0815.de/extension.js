import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import GObject from 'gi://GObject';
import St from 'gi://St';

import { Extension } from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';

const GpTouchMenu = GObject.registerClass(
class GpTouchMenu extends PanelMenu.Button {
    _init(scriptPath) {
        super._init(0.0, 'GpTouch');
        this._scriptPath = scriptPath;

        // Passendes Icon für Rotation aus dem System-Theme laden
        const icon = new St.Icon({
            icon_name: 'rotation-allowed-symbolic',
            style_class: 'system-status-icon',
        });
        this.add_child(icon);

        // Menüeinträge für die 4 Orientierungen erstellen
        this._addOrientationItem('Landscape (Normal)', 1);
        this._addOrientationItem('Portrait (Right side up)', 2);
        this._addOrientationItem('Portrait (Left side up)', 3);
        this._addOrientationItem('Inverted (Inverted)', 4);
    }

    _addOrientationItem(label, orientationValue) {
        // addAction ist die kompakte Kurzform für PopupMenuItem + connect('activate')
        this.menu.addAction(label, () => {
            this._rotate(orientationValue);
        });
    }

    _rotate(orientationValue) {
        try {
            const pythonArgs = [
                'python3',
                this._scriptPath,
                '-o',
                String(orientationValue),
                '--skip-reboot',
            ];

            let argv = null;

            // Prüft moderne & klassische GNOME-Terminals der Reihe nach
            if (GLib.find_program_in_path('ptyxis')) {
                argv = ['ptyxis', '--', ...pythonArgs];
            } else if (GLib.find_program_in_path('kgx')) {
                argv = ['kgx', '--', ...pythonArgs];
            } else if (GLib.find_program_in_path('gnome-terminal')) {
                argv = ['gnome-terminal', '--', ...pythonArgs];
            } else if (GLib.find_program_in_path('xdg-terminal-exec')) {
                argv = ['xdg-terminal-exec', ...pythonArgs];
            } else {
                const msg = 'Kein unterstütztes Terminal (ptyxis, kgx, gnome-terminal) gefunden!';
                console.error(`GpTouch Fehler: ${msg}`);
                Main.notifyError('GpTouch Fehler', msg);
                return;
            }

            // Startet den Prozess sicher ohne Shell-String-Parsing
            const proc = Gio.Subprocess.new(argv, Gio.SubprocessFlags.NONE);
            proc.wait_async(null, null);

            console.log(`GpTouch Extension: Ausgeführt -> ${argv.join(' ')}`);
        } catch (e) {
            console.error(`GpTouch Extension Fehler: ${e.message}`);
            Main.notifyError('GpTouch Fehler', e.message);
        }
    }
});

export default class GpTouchExtension extends Extension {
    enable() {
        const scriptPath = this.dir.get_child('gptouch.py').get_path();

        this._indicator = new GpTouchMenu(scriptPath);
        Main.panel.addToStatusArea(this.uuid, this._indicator);
    }

    disable() {
        this._indicator?.destroy();
        this._indicator = null;
    }
}
