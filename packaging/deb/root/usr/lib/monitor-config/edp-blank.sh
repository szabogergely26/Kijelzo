#!/bin/bash
# eDP (laptop-panel) háttérvilágítás elsötétítése / visszaállítása.
#
# Kézi kapcsolóhoz készült (a plasmoid switch-éhez, systemctl --user start/stop
# edp-blank.service formában hívva) — NEM idle-alapú automatika. A "Laptop +
# Soundbar" profilnál a Soundbar csak hang-útvonal, nem valódi kijelző, ott az
# eDP az egyetlen valós kép — ott ezt nem szabad indítani. "Laptop + TV +
# Soundbar" alatt viszont a laptop panelje felesleges, azt kapcsolja le a
# felhasználó kézzel, amíg TV-t néz.
#
# A brightness írásához nem kell root/sudo: a systemd-logind saját, a session
# tulajdonos felhasználójának engedélyezett SetBrightness D-Bus hívásán megy,
# nem közvetlen /sys/class/backlight írással (az root:root, sima userként nem
# írható).

set -euo pipefail

CONFIG_DIR="$HOME/.config/monitor-config"
STATE_FILE="$CONFIG_DIR/edp-brightness-saved"

backlight_dir="$(find /sys/class/backlight -mindepth 1 -maxdepth 1 -print -quit)"
if [ -z "$backlight_dir" ]; then
    echo "Nincs elérhető backlight eszköz (/sys/class/backlight üres)." >&2
    exit 1
fi
backlight_name="$(basename "$backlight_dir")"

: "${XDG_SESSION_ID:?XDG_SESSION_ID nincs beállítva — nem systemd-logind által kezelt munkamenet?}"
session_path="/org/freedesktop/login1/session/${XDG_SESSION_ID}"

set_brightness() {
    busctl --system call org.freedesktop.login1 "$session_path" \
        org.freedesktop.login1.Session SetBrightness ssu backlight "$backlight_name" "$1" >/dev/null
}

case "${1:-}" in
    set)
        mkdir -p "$CONFIG_DIR"
        cat "$backlight_dir/brightness" > "$STATE_FILE"
        set_brightness 0
        ;;
    restore)
        if [ -f "$STATE_FILE" ]; then
            saved="$(cat "$STATE_FILE")"
        else
            saved="$(cat "$backlight_dir/max_brightness")"
        fi
        set_brightness "$saved"
        ;;
    *)
        echo "Használat: $0 {set|restore}" >&2
        exit 2
        ;;
esac
