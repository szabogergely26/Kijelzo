# -*- coding: utf-8 -*-
"""
Kijelző beállítások — főablak (PySide6).

A tényleges profilváltás-logika a `.app` modulban van (Qt-független) —
ez a fájl csak a megjelenítést és a felhasználói interakciót kezeli.

Layout (2026-09-11 véglegesített terv):
  1. Címsor: "Kijelző beállítások" (+ halvány telepített/dev jelző)
  2. Státuszsor: jelenlegi KScreen állapot, mindig látható
  3. Két másodlagos gomb: Automatikus felismerés / Kijelzők újrafelvétele
  4. Három nagy profil-csempe egymás mellett
  5. Elválasztó vonal
  6. Két harmadlagos gomb 2 oszlopos rácsban: Asztal helyreállítása / Hibaelhárítás
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))
    __package__ = "monitor_config"

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QKeySequence, QShortcut, QPixmap
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from .app import (
    DRY_RUN,
    build_kscreen_command,
    classify_live_outputs,
    has_kscreen_doctor,
    live_detection_available,
    parse_kscreen_text,
    run_sequence,
)
from .autodetect import detect_current_kscreen_setup, detect_saved_kscreen_setup
from .command_utils import run_cmd
from .config import LOG_FILE_PATH
from .kscreen_input import clear_kscreen_input_file, has_usable_kscreen_input
from .log_utils import log, log_open
from .notifications import init_notifications, notify
from .plasma_utils import restart_plasmashell_detached
from .profiles import PROFILE_ALL, PROFILE_LAPTOP, PROFILE_LAPTOP_SOUNDBAR
from .setup_dialog import KScreenFirstRunDialog
from .troubleshoot_window import TroubleshootWindow
from .version_info import APP_NAME, APP_VERSION, get_window_title

# A GUI-ban megjelenített nevek — ugyanaz a térkép, mint a cli.py-ban.
DISPLAY_NAMES = {
    PROFILE_LAPTOP: "Laptop mód",
    PROFILE_LAPTOP_SOUNDBAR: "Laptop mód + Zene",
    PROFILE_ALL: "Film / Sorozat mód",
}

PROFILE_SUBTITLES = {
    PROFILE_LAPTOP: "Csak a beépített kijelző",
    PROFILE_LAPTOP_SOUNDBAR: "Kijelző + Harman Kardon",
    PROFILE_ALL: "TV + Harman Kardon",
}

# Melyik csempéhez melyik SVG-ikon tartozik (monitor_config/assets/icons/ alatt).
PROFILE_ICON_FILES = {
    PROFILE_LAPTOP: "laptop_mode.png",
    PROFILE_LAPTOP_SOUNDBAR: ["laptop_mode.png", "soundbar.png"],
    PROFILE_ALL: ["laptop_mode.png", "tv.png", "soundbar.png"],
}

ICONS_DIR = Path(__file__).resolve().parent / "assets" / "icons"


def _is_installed_instance() -> bool:
    """
    Igaz, ha ez a folyamat a telepített (.deb-ből származó,
    /usr/... alá telepített) csomagból fut, hamis, ha dev-forrásból.
    """
    try:
        return str(Path(__file__).resolve()).startswith("/usr/")
    except Exception:
        return False


# --------------------------------------------------------------------------- #
# Névjegy
# --------------------------------------------------------------------------- #

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Névjegy – {APP_NAME}")
        self.setModal(True)
        self.setMinimumSize(420, 380)

        origin = "telepített (.deb)" if _is_installed_instance() else "fejlesztői forrás"

        text = f"""
<h2 style="margin-bottom:0">{APP_NAME}</h2>
<div>Verzió: <b>{APP_VERSION}</b></div>
<div>Futási hely: <b>{origin}</b></div>
<p><b>Lenovo-ThinkPad</b> laptop-hoz tartozik</p>
<hr/>
<p>Gyors kijelző-profil váltó KDE Wayland/X11 környezethez.</p>

<ul>
  <li>KDE X11/Wayland: <code>kscreen-doctor</code> (ID-alapú)</li>
  <li>Értesítés: libnotify/KNotification</li>
  <li>Automatikus felismerés</li>
  <li>Napló: <code>{LOG_FILE_PATH}</code></li>
</ul>
<small>&copy; 2026. szeptember – saját használatra</small>
"""
        view = QTextBrowser(self)
        view.setOpenExternalLinks(True)
        view.setHtml(text)
        view.setFrameShape(QFrame.Shape.NoFrame)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, parent=self)
        btns.button(QDialogButtonBox.StandardButton.Close).setText("Bezárás")
        btns.rejected.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.addWidget(view)
        lay.addWidget(btns)


# --------------------------------------------------------------------------- #
# Profil-ikon (SVG-fájlból betöltve)
# --------------------------------------------------------------------------- #

class ProfileGlyph(QWidget):
    """
    Profil-csempe ikon konténer.
    Képes kezelni egyetlen képet (str) és képek listáját (list[str]) is.
    """
    def __init__(self, icon_files, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Ha egyetlen sztringet kapott, listává alakítjuk
        if isinstance(icon_files, str):
            icon_files = [icon_files]
        elif not icon_files:
            icon_files = []

        for icon_filename in icon_files:
            icon_path = ICONS_DIR / icon_filename
            lbl = QLabel()
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            if icon_path.exists():
                pixmap = QPixmap(str(icon_path))
                # Fix 45x45 skálázás élsimítással
                scaled_pixmap = pixmap.scaled(
                    QSize(45, 45),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                lbl.setPixmap(scaled_pixmap)
            else:
                print(f"[FIGYELMEZTETÉS] A kép nem található: {icon_path}")

            layout.addWidget(lbl)

# --------------------------------------------------------------------------- #
# Profil-csempe
# --------------------------------------------------------------------------- #

class ProfileTile(QFrame):
    """Egy nagy, kattintható profil-csempe (ikon + cím + alcím)."""

    def __init__(self, profile_name: str, parent=None):
        super().__init__(parent)
        self.profile_name = profile_name
        self._active = False

        self.setObjectName("tile")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumHeight(140)
        self.setMinimumWidth(200)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 18, 14, 14)
        lay.setSpacing(10)
        lay.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        icon_filename = PROFILE_ICON_FILES.get(profile_name)
        self.icon_glyph = ProfileGlyph(icon_filename)

        glyph_row = QHBoxLayout()
        glyph_row.addStretch(1)
        glyph_row.addWidget(self.icon_glyph)
        glyph_row.addStretch(1)

        self.title_label = QLabel(DISPLAY_NAMES.get(profile_name, profile_name))
        self.title_label.setObjectName("tileTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.sub_label = QLabel(PROFILE_SUBTITLES.get(profile_name, ""))
        self.sub_label.setObjectName("tileSub")
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_label.setWordWrap(True)

        lay.addLayout(glyph_row)
        lay.addWidget(self.title_label)
        lay.addWidget(self.sub_label)

        self.on_click = None  # a MainWindow állítja be

    def set_active(self, active: bool):
        self._active = active
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.on_click is not None:
            self.on_click()
        super().mouseReleaseEvent(event)


# --------------------------------------------------------------------------- #
# Főablak
# --------------------------------------------------------------------------- #

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.log_file = log_open()
        self.troubleshoot_window: TroubleshootWindow | None = None

        self.setWindowTitle(get_window_title(DRY_RUN))
        self.setMinimumWidth(820)
        self.resize(880, 480)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 16)
        root.setSpacing(14)

        # -- Címsor (saját, mert a jelzőt is bele kell tenni) --------------- #
        titlebar = QHBoxLayout()
        titlebar.setSpacing(8)

        title_lbl = QLabel("Kijelző beállítások")
        title_lbl.setObjectName("windowTitle")

        self.origin_tag = QLabel(
            "telepített" if _is_installed_instance() else "fejlesztői"
        )
        self.origin_tag.setObjectName("originTag")
        self.origin_tag.setToolTip(
            "Ez a példány a "
            + ("telepített (.deb) csomagból" if _is_installed_instance() else "fejlesztői forrásból")
            + " fut."
        )

        help_btn = QPushButton()
        help_btn.setFlat(True)
        help_btn.setToolTip("Névjegy")
        ico = QIcon.fromTheme("help-about")
        if not ico.isNull():
            help_btn.setIcon(ico)
        else:
            help_btn.setText("ℹ")
        help_btn.clicked.connect(self.show_about)

        titlebar.addWidget(title_lbl, 1, Qt.AlignmentFlag.AlignVCenter)
        titlebar.addWidget(self.origin_tag, 0, Qt.AlignmentFlag.AlignVCenter)
        titlebar.addWidget(help_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        root.addLayout(titlebar)

        # -- Státuszsor (mindig látható) ------------------------------------ #
        self.status_bar = QFrame()
        self.status_bar.setObjectName("statusBar")
        sb_lay = QHBoxLayout(self.status_bar)
        sb_lay.setContentsMargins(14, 10, 14, 10)
        self.status_dot = QLabel("●")
        self.status_dot.setObjectName("statusDot")
        self.sb_msg = QLabel("Aktuális állapot: lekérdezés…")
        self.sb_msg.setObjectName("statusText")
        sb_lay.addWidget(self.status_dot)
        sb_lay.addWidget(self.sb_msg, 1)
        root.addWidget(self.status_bar)

        # -- Másodlagos gombok ------------------------------------------------ #
        secondary_row = QHBoxLayout()
        secondary_row.setSpacing(10)
        self.b_auto = QPushButton("Automatikus felismerés")
        self.b_auto.setObjectName("secondaryButton")
        self.b_relearn = QPushButton("Kijelzők újrafelvétele")
        self.b_relearn.setObjectName("secondaryButton")
        self.b_relearn.setToolTip("Mentett KScreen bemenet törlése és új kijelzőfelvétel indítása.")
        secondary_row.addWidget(self.b_auto)
        secondary_row.addWidget(self.b_relearn)
        root.addLayout(secondary_row)

        # -- Profil-csempék ---------------------------------------------------- #
        tiles_row = QHBoxLayout()
        tiles_row.setSpacing(12)
        self.tiles: dict[str, ProfileTile] = {}
        for profile_name in (PROFILE_LAPTOP, PROFILE_LAPTOP_SOUNDBAR, PROFILE_ALL):
            tile = ProfileTile(profile_name)
            tile.on_click = lambda p=profile_name: self.apply_profile(p)
            tiles_row.addWidget(tile)
            self.tiles[profile_name] = tile
        root.addLayout(tiles_row)

        # -- Elválasztó ---------------------------------------------------- #
        divider = QFrame()
        divider.setObjectName("divider")
        divider.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(divider)

        # -- Harmadlagos gombok (2 oszlopos rács) --------------------------- #
        tertiary_row = QHBoxLayout()
        tertiary_row.setSpacing(10)
        self.b_restart_shell = QPushButton("Asztal helyreállítása")
        self.b_restart_shell.setObjectName("tertiaryButton")
        self.b_restart_shell.setToolTip(
            "Csak a plasmashell újraindítása, kijelző-profilváltás nélkül — akkor "
            "hasznos, ha az asztal (háttér/ikonok) elszállt, de a panel még megy."
        )
        self.b_troubleshoot = QPushButton("Hibaelhárítás")
        self.b_troubleshoot.setObjectName("tertiaryButton")
        tertiary_row.addWidget(self.b_restart_shell)
        tertiary_row.addWidget(self.b_troubleshoot)
        root.addLayout(tertiary_row)

        # -- Signálok -------------------------------------------------------- #
        self.b_auto.clicked.connect(self.auto_detect_and_apply)
        self.b_relearn.clicked.connect(self.relearn_displays)
        self.b_restart_shell.clicked.connect(self.restart_shell)
        self.b_troubleshoot.clicked.connect(self.open_troubleshoot)

        QShortcut(QKeySequence(QKeySequence.StandardKey.HelpContents), self, activated=self.show_about)

        self.setStyleSheet(QSS)

        self._refresh_auto_button_text()
        self._init_current_status()

        # A profilalkalmazás minden támogatott munkamenetben KScreenen keresztül történik.
        if not has_kscreen_doctor(self.log_file):
            self.sb_msg.setText("HIBA: 'kscreen-doctor' nem érhető el (KDE/Plasma szükséges).")

    # ----------------------------------------------------------------- #
    # Segéd: aktív csempe kiemelése
    # ----------------------------------------------------------------- #

    def _highlight_active_tile(self, profile_name: str | None):
        for name, tile in self.tiles.items():
            tile.set_active(name == profile_name)

    # ----------------------------------------------------------------- #
    # Állapot
    # ----------------------------------------------------------------- #

    def _init_current_status(self):
        """
        Induláskori státusz a pillanatnyi, engedélyezett KScreen-kimenetekből.
        Élőben kerül lekérdezésre, nem függ a mentett fájltól.
        """
        try:
            log(self.log_file, "[DETECT] aktuális profil forrása: élő KScreen állapot")

            rc, live_text, err = run_cmd("kscreen-doctor -o", self.log_file)
            if rc != 0:
                raise RuntimeError(err.strip() or "A kscreen-doctor -o lekérdezés sikertelen.")

            profile_name, detail = detect_current_kscreen_setup(live_text, self.log_file)
            display_name = DISPLAY_NAMES.get(profile_name, profile_name)

            self.sb_msg.setText(f"Aktuális állapot: {display_name} · {detail}")
            self._highlight_active_tile(profile_name)
            log(self.log_file, f"[STARTUP] current_profile={profile_name}")
            log(self.log_file, f"[STARTUP] current_detail={detail}")

        except Exception as e:
            log(self.log_file, f"[STARTUP] saved detect FAIL: {e}")
            self.sb_msg.setText("Aktuális állapot: ismeretlen")

    # ----------------------------------------------------------------- #
    # Profilváltás
    # ----------------------------------------------------------------- #

    def apply_profile(self, name: str):
        if not live_detection_available(self.log_file) and not has_usable_kscreen_input():
            log(
                self.log_file,
                "[KSCREEN-INPUT] profil alkalmazása tiltva: sem élőben, sem mentett "
                "fájlból nem azonosítható a laptop-kijelző",
            )
            self.sb_msg.setText("Aktuális állapot: a laptop-kijelző nem azonosítható.")
            notify(
                "Kijelző nem azonosítható",
                "Sem élőben, sem a mentett kscreen-input.txt-ből nem azonosítható "
                "egyértelműen a laptop-kijelző.",
                "normal",
                4000,
                self.log_file,
            )
            self._refresh_auto_button_text()
            return

        display_name = DISPLAY_NAMES.get(name, name)
        self.sb_msg.setText(f"A(z) „{display_name}” profil alkalmazása…")
        QApplication.processEvents()
        self._set_buttons_enabled(False)
        try:
            if not has_kscreen_doctor(self.log_file):
                notify("Kijelző hiba", "A 'kscreen-doctor' nem érhető el.", "critical", 8000, self.log_file)
                return

            log(self.log_file, f"[APPLY] profile={name}, DRY_RUN={DRY_RUN}, backend=kscreen-doctor")
            command = build_kscreen_command(name, self.log_file)
            log(self.log_file, f"[APPLY] generated={command}")
            ok, msg = run_sequence([command], self.log_file)

            if ok and DRY_RUN:
                log(self.log_file, "[DRY] would restart plasmashell (profilváltás után)")
            elif ok:
                log(self.log_file, "[PLASMA] újraindítás minden profilváltás után (asztal-konténer hiba elkerülése)")
                restart_plasmashell_detached(self.log_file)

                self.sb_msg.setText(f"Aktuális állapot: {display_name}")
                self._highlight_active_tile(name)
                notify("Kijelző beállítva", "Profil alkalmazva (KScreen).", "normal", 4000, self.log_file)
            else:
                notify("Kijelző hiba", msg if isinstance(msg, str) else str(msg), "critical", 8000, self.log_file)

        except Exception as e:
            log(self.log_file, "EXC:", repr(e))
            log(self.log_file, traceback.format_exc())
            notify("Kijelző kivétel", str(e), "critical", 8000, self.log_file)
        finally:
            self._refresh_auto_button_text()

    def auto_detect_and_apply(self):
        self._refresh_auto_button_text()
        self.sb_msg.setText("Kijelzők felismerése…")
        QApplication.processEvents()
        self._set_buttons_enabled(False)

        try:
            rc, live_text, err = run_cmd("kscreen-doctor -o", self.log_file)
            if rc != 0:
                raise RuntimeError(err.strip() or "A kscreen-doctor -o lekérdezés sikertelen.")

            if classify_live_outputs(parse_kscreen_text(live_text)) is not None:
                profile_name, detail = detect_current_kscreen_setup(live_text, self.log_file)
                log(self.log_file, "[AUTODETECT] forrás: élő KScreen állapot")
            elif has_usable_kscreen_input():
                profile_name, detail = detect_saved_kscreen_setup(self.log_file)
                log(self.log_file, "[AUTODETECT] forrás: mentett KScreen bemenet (élő azonosítás nem egyértelmű)")
            else:
                raise RuntimeError(
                    "A laptop-kijelző élőben nem azonosítható, és nincs használható mentett KScreen bemenet sem."
                )

            log(self.log_file, f"[AUTODETECT] selected_profile={profile_name}")
            log(self.log_file, f"[AUTODETECT] detail={detail}")

            notify("Autodetect", f"{detail}\n→ {DISPLAY_NAMES.get(profile_name, profile_name)}", "normal", 3500, self.log_file)

            self.apply_profile(profile_name)

        except Exception as e:
            log(self.log_file, "AUTODETECT EXC:", repr(e))
            log(self.log_file, traceback.format_exc())
            notify("Autodetect hiba", str(e), "critical", 8000, self.log_file)
            self.sb_msg.setText("Aktuális állapot: autodetect hiba történt.")
        finally:
            self._refresh_auto_button_text()

    def relearn_displays(self):
        try:
            path = clear_kscreen_input_file()
            log(self.log_file, f"[KSCREEN-INPUT] mentett KScreen bemeneti fájl előkészítve: {path}")

            self.sb_msg.setText(
                "Mentett KScreen bemenet előkészítve. Másold be a kscreen-doctor -o "
                "teljes kimenetét a fájlba."
            )
            self._refresh_auto_button_text()

            KScreenFirstRunDialog(self).exec()

            self._refresh_auto_button_text()

        except Exception as e:
            log(self.log_file, f"[KSCREEN-INPUT] újrafelvétel hiba: {e}")
            notify("Kijelzők újrafelvétele hiba", str(e), "critical", 6000, self.log_file)

    def restart_shell(self):
        """
        Önálló asztal-helyreállítás: csak a plasmashell újraindítása,
        kijelző-profilváltás nélkül.
        """
        self.sb_msg.setText("Aktuális állapot: asztal helyreállítása (plasmashell újraindítása)…")
        QApplication.processEvents()
        self.b_restart_shell.setEnabled(False)
        try:
            log(self.log_file, "[PLASMA] kézi asztal-helyreállítás kérve (GUI)")
            restart_plasmashell_detached(self.log_file)
            notify("Asztal helyreállítása", "A plasmashell újraindítása folyamatban.", "normal", 4000, self.log_file)
        finally:
            self.b_restart_shell.setEnabled(True)
            self._init_current_status()

    def open_troubleshoot(self):
        if self.troubleshoot_window is None:
            self.troubleshoot_window = TroubleshootWindow(self.log_file, parent=self)
        self.troubleshoot_window.show()
        self.troubleshoot_window.raise_()
        self.troubleshoot_window.activateWindow()

    # ----------------------------------------------------------------- #
    # Egyéb
    # ----------------------------------------------------------------- #

    def _refresh_auto_button_text(self):
        try:
            has_live = live_detection_available(self.log_file)
            has_saved = has_usable_kscreen_input()
            can_apply = has_live or has_saved

            if has_live:
                self.b_auto.setText("Automatikus felismerés")
                self.b_auto.setToolTip(
                    "Profil felismerése és alkalmazása a jelenleg csatlakoztatott "
                    "kijelzők élő állapota (max. felbontás) alapján."
                )
            elif has_saved:
                self.b_auto.setText("Felismerés fájlból")
                self.b_auto.setToolTip(
                    "Élő felismerés nem egyértelmű. Profil felismerése a mentett "
                    "kscreen-input.txt fájlból."
                )
            else:
                self.b_auto.setText("Kijelző nem azonosítható")
                self.b_auto.setToolTip(
                    "Sem élőben, sem mentett fájlból nem azonosítható egyértelműen a "
                    "laptop-kijelző. Használd a „Kijelzők újrafelvétele” gombot."
                )

            for tile in self.tiles.values():
                tile.setEnabled(can_apply)
            self.b_auto.setEnabled(can_apply)
            self.b_relearn.setEnabled(True)

        except Exception as e:
            log(self.log_file, f"[KSCREEN-INPUT] button refresh FAIL: {e}")
            self.b_auto.setText("Kijelző nem azonosítható")
            for tile in self.tiles.values():
                tile.setEnabled(False)
            self.b_auto.setEnabled(False)
            self.b_relearn.setEnabled(True)

    def _set_buttons_enabled(self, enabled: bool):
        for tile in self.tiles.values():
            tile.setEnabled(enabled)
        self.b_auto.setEnabled(enabled)
        self.b_relearn.setEnabled(True)

    def show_about(self):
        try:
            AboutDialog(self).exec()
            log(self.log_file, "About opened")
        except Exception as e:
            log(self.log_file, f"About FAIL: {e}")
            notify("Névjegy hiba", str(e), "critical", 6000, self.log_file)

    def closeEvent(self, ev):
        try:
            self.log_file.close()
        except Exception:
            pass
        super().closeEvent(ev)


# --------------------------------------------------------------------------- #
# Stílus (Breeze-közeli, kék akcent — a jóváhagyott mockup alapján)
# --------------------------------------------------------------------------- #

QSS = """
QWidget            { background: #eef0f2; color: #1b1e24;
                     font-family: "Noto Sans"; font-size: 12.5px; }

QLabel#windowTitle  { font-size: 15px; font-weight: 600; }
QLabel#originTag    { color: #9aa0a8; font-size: 10.5px; }

QFrame#statusBar    { background: #ffffff; border: 1px solid #d7dbe0;
                      border-radius: 8px; }
QFrame#statusBar QWidget { background: transparent; }
QLabel#statusDot    { color: #1f9d55; font-size: 10px; padding-right: 4px; background: transparent; }
QLabel#statusText   { color: #1b1e24; background: transparent; }

QPushButton#secondaryButton {
    background: #ffffff; border: 1px solid #d7dbe0; border-radius: 8px;
    padding: 9px 12px;
}
QPushButton#secondaryButton:hover  { background: #f5f8fc; border-color: #b9c4d4; }
QPushButton#secondaryButton:pressed { background: #e8ecf0; }

QFrame#tile {
    background: #ffffff; border: 1.5px solid #d7dbe0; border-radius: 12px;
}
QFrame#tile:hover { border-color: #aebbcc; }
QFrame#tile[active="true"] { border-color: #2563eb; background: #e8f0fe; }

/* A csempén belüli minden gyerek widget hátterét átlátszóra állítjuk,
   különben a globális QWidget háttérszín (#eef0f2) "átüt" az ikonok
   és a szövegek körül, szürke keretes hatást okozva. */
QFrame#tile QWidget { background: transparent; }

QLabel#tileTitle { font-size: 13.5px; font-weight: 600; background: transparent; }
QFrame#tile[active="true"] QLabel#tileTitle { color: #2563eb; }
QLabel#tileSub   { font-size: 11px; color: #6b7280; background: transparent; }

QFrame#divider { background: #d7dbe0; max-height: 1px; border: none; }

QPushButton#tertiaryButton {
    background: transparent; border: 1px solid #d7dbe0; border-radius: 8px;
    padding: 10px 12px; color: #6b7280;
}
QPushButton#tertiaryButton:hover   { background: #e4e7eb; color: #1b1e24; }
QPushButton#tertiaryButton:pressed { background: #d7dbe0; }
"""


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #

def main():
    app = QApplication(sys.argv)
    init_notifications()
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
