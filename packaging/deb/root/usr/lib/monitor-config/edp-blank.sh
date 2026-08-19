#!/bin/bash
# eDP (laptop-panel) háttérvilágítás automatikus elsötétítése idle esetén.
#
# A plasmoid switch-e a "watch" módot indítja/állítja le (systemctl --user
# start/stop edp-blank.service). Amíg fut: ha IDLE_THRESHOLD mp-ig nincs
# billentyű/egér-aktivitás, elsötétíti a panelt; bármilyen aktivitásra
# azonnal visszaáll, majd a ciklus ismétlődik. Leállításkor (systemctl stop,
# SIGTERM) a trap biztosítja, hogy ha éppen sötét volt, visszaálljon.
#
# Az IDLE_THRESHOLD (és POLL_INTERVAL) értéke a
# ~/.config/monitor-config/edp-blank.conf fájlból felülírható — ott
# módosítsd, NE ebben a fájlban (ez .deb-frissítéskor felülíródik).
#
# A "Laptop + Soundbar" profilnál a Soundbar csak hang-útvonal, nem valódi
# kijelző, ott az eDP az egyetlen valós kép — ott ezt a felhasználó nem
# indítja el. "Laptop + TV + Soundbar" alatt viszont a laptop panelje
# felesleges, azt kapcsolja idle esetén automatikusan sötétre.
#
# A brightness írásához nem kell root/sudo: a systemd-logind saját, a session
# tulajdonos felhasználójának engedélyezett SetBrightness D-Bus hívásán megy,
# nem közvetlen /sys/class/backlight írással (az root:root, sima userként nem
# írható). Az idle-időt a KDE (ksmserver) org.freedesktop.ScreenSaver
# GetSessionIdleTime hívása adja, szintén root nélkül.

set -euo pipefail

CONFIG_DIR="$HOME/.config/monitor-config"
STATE_FILE="$CONFIG_DIR/edp-brightness-saved"
USER_CONF="$CONFIG_DIR/edp-blank.conf"

# Alapértékek — a /usr/lib alatti script .deb-frissítéskor felülíródik, ezért
# a tényleges testreszabás a USER_CONF fájlban él, azt sose írja felül semmi.
IDLE_THRESHOLD=180  # mp inaktivitás, ami után elsötétít
POLL_INTERVAL=1     # mp, ilyen gyakran ellenőrzi az idle-időt

# shellcheck source=/dev/null
[ -f "$USER_CONF" ] && . "$USER_CONF"

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

get_idle_seconds() {
    # A KDE (ksmserver) GetSessionIdleTime-ja ezredmásodpercet ad vissza, NEM
    # másodpercet (eltér a freedesktop-spec névleges "seconds" leírásától) —
    # ezért osztjuk 1000-rel, mielőtt a másodperc-alapú küszöbhöz hasonlítjuk.
    local idle_ms
    idle_ms="$(busctl --user call org.freedesktop.ScreenSaver /ScreenSaver \
        org.freedesktop.ScreenSaver GetSessionIdleTime 2>/dev/null | awk '{print $2}')"
    echo $(( ${idle_ms:-0} / 1000 ))
}

dimmed=false

restore_if_dimmed() {
    if [ "$dimmed" = true ] && [ -f "$STATE_FILE" ]; then
        set_brightness "$(cat "$STATE_FILE")"
    fi
}

case "${1:-watch}" in
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
    watch)
        mkdir -p "$CONFIG_DIR"
        trap 'restore_if_dimmed; exit 0' TERM INT

        while true; do
            idle="$(get_idle_seconds || echo 0)"

            if [ "$dimmed" = false ] && [ "$idle" -ge "$IDLE_THRESHOLD" ]; then
                cat "$backlight_dir/brightness" > "$STATE_FILE"
                set_brightness 0
                dimmed=true
            elif [ "$dimmed" = true ] && [ "$idle" -lt "$IDLE_THRESHOLD" ]; then
                set_brightness "$(cat "$STATE_FILE")"
                dimmed=false
            fi

            sleep "$POLL_INTERVAL" &
            wait $!
        done
        ;;
    *)
        echo "Használat: $0 {watch|set|restore}" >&2
        exit 2
        ;;
esac
