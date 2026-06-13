#!/usr/bin/env python3
import gi, os, sys, subprocess
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

VENDOR_ID  = '1c4f'
PRODUCT_ID = '0002'
UDEV_PATH  = '/etc/udev/rules.d/99-balam-rush.rules'
AUTOSTART  = os.path.expanduser('~/.config/autostart/balam-rush-rgb.desktop')
APP_PATH   = os.path.abspath(__file__)

# Paleta: #0583F2 #F20505 #8C0303 #591818 #262626
CSS = """
* { font-family: 'Ubuntu', 'Noto Sans', sans-serif; }

window { background-color: #1a0a0a; }

.main-box {
    background-color: #f2f2f2;
    padding: 32px;
}

/* Header */
.brand {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 5px;
    color: #591818;
}
.title-keyboard {
    font-size: 28px;
    font-weight: 700;
    color: #612C21;
    letter-spacing: 1px;
}
.title-rgb-on {
    font-size: 28px;
    font-weight: 700;
    color: #639E5F;
    letter-spacing: 1px;
}
.title-rgb-off {
    font-size: 28px;
    font-weight: 700;
    color: #C3C2CF;
    letter-spacing: 1px;
}

/* Status box */
.status-box {
    background-color: #220c0c;
    border-radius: 10px;
    padding: 16px 22px;
    border: 1px solid #3d1414;
}
.dot-on  { color: #639E5F; font-size: 10px; }
.dot-off { color: #FAF0F0; font-size: 10px; }
.txt-on  { font-size: 13px; font-weight: 700; color: #639E5F; letter-spacing: 2px; }
.txt-off { font-size: 13px; font-weight: 700; color: #FAF0F0; letter-spacing: 2px; }

/* Botón encender */
.btn-on {
    background: linear-gradient(135deg, #8C0303, #F20505);
    color: #ffffff;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 3px;
    border-radius: 12px;
    border: none;
    padding: 18px 52px;
    min-width: 220px;
}
.btn-on:hover {
    background: linear-gradient(135deg, #F20505, #ff2222);
}

/* Botón apagado */
.btn-off {
    background-color: #220c0c;
    color: #591818;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 3px;
    border-radius: 12px;
    border: 1px solid #3d1414;
    padding: 18px 52px;
    min-width: 220px;
}
.btn-off:hover {
    background-color: #2e0f0f;
    color: #8C0303;
    border-color: #591818;
}

/* Advertencia permisos */
.warn-box {
    background-color: #0a1a2e;
    border-radius: 10px;
    padding: 14px 18px;
    border: 1px solid #0583F2;
}
.warn-txt {
    font-size: 12px;
    color: #0583F2;
    font-weight: 600;
}
.warn-btn {
    background-color: #0583F2;
    color: #ffffff;
    font-size: 12px;
    font-weight: 700;
    border-radius: 8px;
    border: none;
    padding: 9px 18px;
    letter-spacing: 1px;
}
.warn-btn:hover { background-color: #0066cc; }

/* Footer */
.err  { font-size: 12px; color: #F20505; font-weight: 600; }
.info { font-size: 11px; color: #3a1212; letter-spacing: 1px; }
.chk  { color: #591818; font-size: 12px; }

/* Separador */
separator { background-color: #2e0f0f; min-height: 1px; }
"""

def find_hidraw():
    import glob
    for h in sorted(glob.glob('/dev/hidraw*')):
        idx = h.replace('/dev/hidraw', '')
        try:
            with open(f'/sys/class/hidraw/hidraw{idx}/device/uevent') as f:
                c = f.read().lower()
            if VENDOR_ID in c and PRODUCT_ID in c:
                return h
        except: pass
    return None

def set_rgb(state, hidraw):
    try:
        fd = os.open(hidraw, os.O_RDWR)
        os.write(fd, bytes([0x00, 0x04 if state else 0x00]))
        os.close(fd)
        return True, None
    except PermissionError: return False, "permission"
    except FileNotFoundError: return False, "notfound"
    except Exception as e: return False, str(e)

def udev_ok():
    try:
        with open(UDEV_PATH) as f: return VENDOR_ID in f.read()
    except: return False

def apply_udev():
    rule = f'SUBSYSTEM=="hidraw", ATTRS{{idVendor}}=="{VENDOR_ID}", ATTRS{{idProduct}}=="{PRODUCT_ID}", MODE="0666"'
    script = f'#!/bin/sh\necho \'{rule}\' > {UDEV_PATH}\nudevadm control --reload-rules\nudevadm trigger\n'
    with open('/tmp/balam_udev.sh', 'w') as f: f.write(script)
    os.chmod('/tmp/balam_udev.sh', 0o755)
    return subprocess.run(['pkexec', 'sh', '/tmp/balam_udev.sh'], capture_output=True).returncode == 0

class App(Gtk.Window):
    def __init__(self, autostart=False):
        super().__init__(title="Balam Rush RGB")
        self.state  = False
        self.hidraw = find_hidraw()

        p = Gtk.CssProvider()
        p.load_from_data(CSS.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), p,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self._build_ui()
        self.set_default_size(400, 0)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect('destroy', Gtk.main_quit)
        try: self.set_icon_name('input-keyboard')
        except: pass
        self.show_all()
        if udev_ok(): self.wbox.hide()
        if autostart: GLib.timeout_add(1000, self._auto)

    def _build_ui(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        root.get_style_context().add_class('main-box')
        self.add(root)

        # ── Header ──────────────────────────────────────────────────
        hdr = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        hdr.set_margin_bottom(26)

        brand = Gtk.Label(label="BALAM RUSH")
        brand.get_style_context().add_class('brand')
        brand.set_halign(Gtk.Align.START)

        title_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        kl = Gtk.Label(label="Keyboard")
        kl.get_style_context().add_class('title-keyboard')
        self.rl = Gtk.Label(label="RGB")
        self.rl.get_style_context().add_class('title-rgb-off')
        title_row.pack_start(kl, False, False, 0)
        title_row.pack_start(self.rl, False, False, 0)

        hdr.pack_start(brand, False, False, 0)
        hdr.pack_start(title_row, False, False, 0)
        root.pack_start(hdr, False, False, 0)

        # ── Advertencia permisos ────────────────────────────────────
        self.wbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.wbox.get_style_context().add_class('warn-box')
        self.wbox.set_margin_bottom(22)

        wt = Gtk.Label(label="⚠  Configuración de permisos USB requerida\npara controlar el RGB sin contraseña cada vez.")
        wt.get_style_context().add_class('warn-txt')
        wt.set_line_wrap(True)
        wt.set_halign(Gtk.Align.START)

        wb = Gtk.Button(label="CONFIGURAR PERMISOS  (requiere contraseña de administrador)")
        wb.get_style_context().add_class('warn-btn')
        wb.connect('clicked', self._perms)

        self.wbox.pack_start(wt, False, False, 0)
        self.wbox.pack_start(wb, False, False, 0)
        root.pack_start(self.wbox, False, False, 0)

        # ── Status ──────────────────────────────────────────────────
        sb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        sb.get_style_context().add_class('status-box')
        sb.set_margin_bottom(26)

        self.dot = Gtk.Label(label="●")
        self.dot.get_style_context().add_class('dot-off')
        self.stx = Gtk.Label(label="APAGADO")
        self.stx.get_style_context().add_class('txt-off')
        sb.pack_start(self.dot, False, False, 0)
        sb.pack_start(self.stx, False, False, 0)
        root.pack_start(sb, False, False, 0)

        # ── Botón principal ─────────────────────────────────────────
        br = Gtk.Box()
        br.set_halign(Gtk.Align.CENTER)
        br.set_margin_bottom(18)
        self.btn = Gtk.Button(label="ENCENDER")
        self.btn.get_style_context().add_class('btn-off')
        self.btn.connect('clicked', self._toggle)
        br.pack_start(self.btn, False, False, 0)
        root.pack_start(br, False, False, 0)

        # ── Error ───────────────────────────────────────────────────
        self.el = Gtk.Label(label="")
        self.el.get_style_context().add_class('err')
        self.el.set_halign(Gtk.Align.CENTER)
        self.el.set_line_wrap(True)
        self.el.set_max_width_chars(40)
        self.el.set_margin_bottom(14)
        root.pack_start(self.el, False, False, 0)

        sep = Gtk.Separator()
        sep.set_margin_bottom(16)
        root.pack_start(sep, False, False, 0)

        # ── Footer ──────────────────────────────────────────────────
        ft = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        self.chk = Gtk.CheckButton(label="Encender RGB automáticamente al iniciar sesión")
        self.chk.get_style_context().add_class('chk')
        self.chk.set_active(os.path.exists(AUTOSTART))
        self.chk.connect('toggled', self._autostart_toggle)
        ft.pack_start(self.chk, False, False, 0)

        dl = Gtk.Label(label=f"USB {VENDOR_ID}:{PRODUCT_ID}  ·  {self.hidraw or 'no detectado'}")
        dl.get_style_context().add_class('info')
        dl.set_halign(Gtk.Align.START)
        ft.pack_start(dl, False, False, 0)
        root.pack_start(ft, False, False, 0)

    # ── Acciones ────────────────────────────────────────────────────────────
    def _toggle(self, _):
        if not self.hidraw:
            self.el.set_text("Teclado no detectado. ¿Está conectado?")
            return
        ok, err = set_rgb(not self.state, self.hidraw)
        if ok:
            self.state = not self.state
            self.el.set_text("")
            self._refresh()
        elif err == "permission":
            self.wbox.show()
            self.el.set_text("Sin permisos. Usa el botón azul de arriba.")
        else:
            self.el.set_text(err or "Error desconocido")

    def _perms(self, _):
        if apply_udev():
            self.hidraw = find_hidraw()
            self.wbox.hide()
            self.el.set_text("")
        else:
            self.el.set_text("No se pudo configurar. ¿Cancelaste la contraseña?")

    def _autostart_toggle(self, c):
        if c.get_active():
            os.makedirs(os.path.dirname(AUTOSTART), exist_ok=True)
            with open(AUTOSTART, 'w') as f:
                f.write(f"[Desktop Entry]\nType=Application\nName=Balam Rush RGB\n"
                        f"Exec=python3 {APP_PATH} --autostart\nHidden=false\n"
                        f"NoDisplay=false\nX-GNOME-Autostart-enabled=true\n")
        else:
            try: os.remove(AUTOSTART)
            except: pass

    def _auto(self):
        if self.hidraw:
            ok, _ = set_rgb(True, self.hidraw)
            if ok:
                self.state = True
                self._refresh()
        return False

    def _refresh(self):
        cb = self.btn.get_style_context()
        cd = self.dot.get_style_context()
        cs = self.stx.get_style_context()
        cr = self.rl.get_style_context()
        if self.state:
            self.btn.set_label("APAGAR")
            cb.remove_class('btn-off');       cb.add_class('btn-on')
            self.stx.set_text("ENCENDIDO")
            cs.remove_class('txt-off');       cs.add_class('txt-on')
            cd.remove_class('dot-off');       cd.add_class('dot-on')
            cr.remove_class('title-rgb-off'); cr.add_class('title-rgb-on')
        else:
            self.btn.set_label("ENCENDER")
            cb.remove_class('btn-on');        cb.add_class('btn-off')
            self.stx.set_text("APAGADO")
            cs.remove_class('txt-on');        cs.add_class('txt-off')
            cd.remove_class('dot-on');        cd.add_class('dot-off')
            cr.remove_class('title-rgb-on');  cr.add_class('title-rgb-off')

App(autostart='--autostart' in sys.argv)
Gtk.main()
