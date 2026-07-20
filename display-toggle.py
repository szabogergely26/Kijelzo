#!/usr/bin/env python3
"""
Laptop-kijelző kikapcsolás szolgáltatás - MS-DOS 6.22 stílusú vezérlő menü
"""

import curses
import subprocess

SERVICE = "edp-blank.service"

MENU_ITEMS = [
    "Szolgáltatás Be  (automatikus kijelző elsötétítés idle esetén)",
    "Szolgáltatás Ki  (csak erre a munkamenetre, loginnál újraindul)",
    "Állapot részletesen",
]


def get_status():
    """Lekérdezi, hogy a service fut-e."""
    result = subprocess.run(
        ["systemctl", "--user", "is-active", SERVICE],
        capture_output=True, text=True
    )
    state = result.stdout.strip()
    return state == "active", state


def get_backlight_state():
    """Megnézi, hogy a panel jelenleg elsötétítve van-e (brightness == 0)."""
    try:
        import glob
        devices = glob.glob("/sys/class/backlight/*")
        if not devices:
            return "N/A"
        with open(f"{devices[0]}/brightness") as f:
            value = int(f.read().strip())
        return "Blanked" if value == 0 else "Active"
    except Exception:
        return "N/A"


def get_hdmi_state():
    """xrandr-ral megnézi, van-e csatlakoztatott és aktív HDMI kimenet."""
    try:
        result = subprocess.run(
            ["xrandr", "--query"], capture_output=True, text=True, timeout=2
        )
        lines = [l for l in result.stdout.splitlines() if "HDMI" in l]
        if not lines:
            return "Nincs HDMI kimenet"
        for line in lines:
            if " connected" in line:
                return "Active" if "(" not in line.split(" connected")[0] else "Active"
        return "Disconnected"
    except Exception:
        return "N/A"


def get_soundbar_state():
    """pactl-lal megnézi, van-e futó (RUNNING) audio sink (pl. USB-C soundbar)."""
    try:
        result = subprocess.run(
            ["pactl", "list", "short", "sinks"], capture_output=True, text=True, timeout=2
        )
        if not result.stdout.strip():
            return "N/A"
        return "Active (playing)" if "RUNNING" in result.stdout else "Idle / Suspended"
    except Exception:
        return "N/A"


def apply_choice(index):
    """Végrehajtja a kiválasztott műveletet."""
    if index == 0:
        subprocess.run(["systemctl", "--user", "start", SERVICE])
    elif index == 1:
        subprocess.run(["systemctl", "--user", "stop", SERVICE])


def draw_status_detail(stdscr):
    """Külön képernyő a részletes állapotnak, bármely gombra visszalép."""
    curses.curs_set(0)
    stdscr.nodelay(False)
    stdscr.erase()

    is_active, raw_state = get_status()
    backlight = get_backlight_state()
    hdmi = get_hdmi_state()
    soundbar = get_soundbar_state()

    title = "Allapot reszletesen"
    stdscr.addstr(1, 2, title, curses.color_pair(1) | curses.A_BOLD)
    stdscr.addstr(2, 2, "=" * len(title), curses.color_pair(1))

    rows = [
        ("Service:", "ACTIVE" if is_active else "INACTIVE", curses.color_pair(3) if is_active else curses.color_pair(4)),
        ("Idle timer:", "ON" if is_active else "OFF", curses.color_pair(3) if is_active else curses.color_pair(4)),
        ("eDP:", backlight, curses.color_pair(1)),
        ("HDMI:", hdmi, curses.color_pair(1)),
        ("Soundbar:", soundbar, curses.color_pair(1)),
    ]

    for i, (label, value, color) in enumerate(rows):
        y = 5 + i
        stdscr.addstr(y, 4, f"{label:<14}", curses.color_pair(1))
        stdscr.addstr(y, 18, value, color | curses.A_BOLD)

    h, w = stdscr.getmaxyx()
    stdscr.addstr(h - 2, 2, "Barmely gomb = Vissza", curses.color_pair(1))
    stdscr.refresh()
    stdscr.getch()


def draw_menu(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()

    # Pár szín-tükrözés a DOS-os kinézethez
    curses.init_pair(1, curses.COLOR_WHITE, -1)          # normál szöveg
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)  # kijelölt sor (invertált)
    curses.init_pair(3, curses.COLOR_GREEN, -1)          # aktív állapot
    curses.init_pair(4, curses.COLOR_RED, -1)            # inaktív állapot

    current_row = 0

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()

        # Cím
        title = "Laptop-kijelzo Energiakezeles - Vezerlopult"
        stdscr.addstr(1, 2, title, curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * len(title), curses.color_pair(1))

        # Menüpontok
        start_y = 5
        for idx, item in enumerate(MENU_ITEMS):
            y = start_y + idx * 2
            label = f" {idx + 1}. {item} "
            if idx == current_row:
                stdscr.addstr(y, 4, label, curses.color_pair(2))
            else:
                stdscr.addstr(y, 4, label, curses.color_pair(1))

        # Állapotsor
        is_active, raw_state = get_status()
        status_y = start_y + len(MENU_ITEMS) * 2 + 2
        stdscr.addstr(status_y, 2, "Allapot: ", curses.color_pair(1))
        if is_active:
            stdscr.addstr("AKTIV (fut)", curses.color_pair(3) | curses.A_BOLD)
        else:
            stdscr.addstr("INAKTIV (leallitva)", curses.color_pair(4) | curses.A_BOLD)

        # Alsó infósor (az F5/F8 sor helyén)
        footer = "Fel/Le=Navigalas  Enter=Valasztas  Q/Esc=Kilepes"
        stdscr.addstr(h - 2, 2, footer, curses.color_pair(1))

        stdscr.refresh()

        key = stdscr.getch()

        if key in (curses.KEY_UP, ord('k')):
            current_row = (current_row - 1) % len(MENU_ITEMS)
        elif key in (curses.KEY_DOWN, ord('j')):
            current_row = (current_row + 1) % len(MENU_ITEMS)
        elif key in (curses.KEY_ENTER, ord('\n'), ord('\r')):
            if current_row == 2:
                draw_status_detail(stdscr)
            else:
                apply_choice(current_row)
        elif key in (ord('1'), ord('2')):
            apply_choice(int(chr(key)) - 1)
        elif key == ord('3'):
            draw_status_detail(stdscr)
        elif key in (ord('q'), ord('Q'), 27):  # 27 = Esc
            break


def main():
    curses.wrapper(draw_menu)


if __name__ == "__main__":
    main()
