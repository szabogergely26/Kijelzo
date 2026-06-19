# Monitor-config / Kijelző profilváltó

Saját használatra készült egyszerű PyQt5 alapú kijelzőprofil-váltó KDE Plasma / X11 környezethez.

A program célja, hogy gyorsan lehessen váltani a ThinkPad kijelző, a Soundbar és a TV között anélkül, hogy minden alkalommal kézzel kellene `xrandr` parancsokat futtatni.

## Állapot

Jelenlegi állapot: működő köztes verzió.

A program jelenleg X11-re van használva.  
A Wayland / `kscreen-doctor` ág a kódban részben jelen van, de jelenleg nincs aktív használatban.

## Jelenlegi célhardver

A program jelenleg az alábbi konkrét felállásra van igazítva:

| Kimenet | Szerep |
|---|---|
| `eDP` | Laptop belső kijelző |
| `HDMI-A-0` | Soundbar / audio útvonalhoz szükséges ál-kijelző |
| `DisplayPort-1` | TV / külső 4K kijelző |

Az automatikus felismerés biztonságosra van tervezve:

> A TV-t nem kapcsoljuk be automatikusan csak azért, mert `connected` állapotban van.

A program helyes működéséhez jelenleg ez a kiosztás az elvárt:


eDP            connected primary
HDMI-A-0       connected / Soundbar
DisplayPort-1  connected / TV


## Fűggőségek

PyQt5



## Debian - KDE csomagok

sudo apt install python3-gi gir1.2-notify-0.7 libnotify-bin



## Jelenlegi struktúra

~/Kijelzo/
  monitor_config.py
  kijelzo.sh
  README.md
  .gitignore
  .venv/



## Fontos megjegyzés

A Soundbar HDMI-eszközként kijelzőnek látszik, de elsődlegesen audio célra van használva.




## Naplófájl

/tmp/monitor_config.log


## Live ellenőrzéshez:

tail -f /tmp/monitor_config.log