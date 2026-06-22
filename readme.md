# Monitor-config / Kijelző profilváltó  - Fejlesztői verzió

Saját használatra készült egyszerű PyQt5 alapú kijelzőprofil-váltó KDE Plasma / X11 környezethez.

A program célja, hogy gyorsan lehessen váltani a ThinkPad kijelző, a Soundbar és a TV között anélkül, hogy minden alkalommal kézzel kellene `xrandr` parancsokat futtatni.

## Állapot

Jelenlegi állapot: működő köztes verzió.

Sajnálatos módon az audió rész instabil, csak az alábbi bekötéssel működik:
  Soundbar - USB-C
  LG TV - HDMI


Ez nem végleges megoldás. Később a program két ismert ThinkPad-konfiguráció közül fog választani.

A teljesen automatikus felismerés jelenleg nem megbízható, ezért a következő lépés két ismert konfiguráció kézi felvétele.

 Következő lépés:
  - Létrehozunk kézzel 2 konfiguráxiót:
      A.
        | Kimenet | Szerep |
        |---      |     ---|
        | `eDP` | Laptop belső kijelző |
        | `USB-C: DisplayPort-1` | Soundbar / audio útvonalhoz szükséges ál-kijelző |
        | `HDMI: HDMI-A-0` | TV / külső 4K kijelző |

      B.
        | Kimenet | Szerep |
        |---      |     ---|
        | `eDP` | Laptop belső kijelző |
        | `HDMI: HDMI-A-0`| Soundbar / audio útvonalhoz szükséges ál-kijelző |
        | `DisplayPort-1` | TV / külső 4K kijelző |

  - Autodetect csak előre beállított profilokból választ



A program jelenleg X11-re van használva.
A Wayland / `kscreen-doctor` ág a kódban részben jelen van, de jelenleg nincs aktív használatban.



## Jelenlegi célhardver

Lenovo ThinkPad E16 Gen2
  - CPU: AMD Ryzen 7
  - GPU: AMD Radeon Graphics 680M


## Fűggőségek

PyQt5



## Debian - KDE csomagok

sudo apt install python3-gi gir1.2-notify-0.7 libnotify-bin







## Fontos megjegyzés

A Soundbar HDMI-eszközként kijelzőnek látszik, de elsődlegesen audio célra van használva.




## Naplófájl

/tmp/monitor_config.log


## Live ellenőrzéshez:

tail -f /tmp/monitor_config.log







## FONTOS!:

## Ismert KDE / TV kijelzőkezelési probléma

A TV-re történő kiterjesztett asztal beállítása KDE Plasma alatt nem mindig működik megbízhatóan.

Fontos megállapítás:
- a hiba nem kizárólag a saját monitor-config scriptben jelentkezik;
- a KDE gyári kijelzőbeállításai is ugyanazt a hibás elrendezést produkálják;
- a Soundbar kikapcsolása / kihúzása után, csak TV-vel is előfordul;
- X11 alatt is jelentkezik.

Következtetés:
A probléma valószínűleg KDE/KScreen, EDID, HDMI/TV vagy driver oldali, nem az alkalmazáslogika hibája.
