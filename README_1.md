# Monitor-config / Kijelző profilváltó — Fejlesztői verzió

Saját használatra készült egyszerű PyQt5 alapú kijelzőprofil-váltó KDE Plasma / X11 környezethez.

A program célja, hogy gyorsan lehessen váltani a ThinkPad kijelző, a Soundbar és a TV között anélkül, hogy minden alkalommal kézzel kellene `xrandr` parancsokat futtatni.

---

## Állapot

**Jelenlegi állapot:** működő köztes verzió.

Sajnálatos módon az audió rész instabil, csak az alábbi bekötéssel működik:

- Soundbar — USB-C
- LG TV — HDMI

Ez nem végleges megoldás. Később a program két ismert ThinkPad-konfiguráció közül fog választani.

A teljesen automatikus felismerés jelenleg nem megbízható, ezért a következő lépés két ismert konfiguráció kézi felvétele.

### Következő lépés

Létrehozunk kézzel 2 konfigurációt:

**A. konfiguráció**

| Kimenet | Szerep |
|---|---|
| `eDP` | Laptop belső kijelző |
| `USB-C: DisplayPort-1` | Soundbar / audio útvonalhoz szükséges ál-kijelző |
| `HDMI: HDMI-A-0` | TV / külső 4K kijelző |

**B. konfiguráció**

| Kimenet | Szerep |
|---|---|
| `eDP` | Laptop belső kijelző |
| `HDMI: HDMI-A-0` | Soundbar / audio útvonalhoz szükséges ál-kijelző |
| `DisplayPort-1` | TV / külső 4K kijelző |

Az autodetect csak előre beállított profilokból választ.

A program jelenleg X11-re van használva. A Wayland / `kscreen-doctor` ág a kódban részben jelen van, de jelenleg nincs aktív használatban.

---

## Jelenlegi célhardver

**Lenovo ThinkPad E16 Gen2**

- CPU: AMD Ryzen 7
- GPU: AMD Radeon Graphics 680M

---

## Függőségek

- PyQt5

### Debian / KDE csomagok

```bash
sudo apt install python3-gi gir1.2-notify-0.7 libnotify-bin
```

---

## Fontos megjegyzés

A Soundbar HDMI-eszközként kijelzőnek látszik, de elsődlegesen audio célra van használva.

---

## Naplófájl

```
/tmp/monitor_config.log
```

### Live ellenőrzéshez

```bash
tail -f /tmp/monitor_config.log
```

---

## ⚠️ FONTOS — Ismert KDE / TV kijelzőkezelési probléma

A TV-re történő kiterjesztett asztal beállítása KDE Plasma alatt nem mindig működik megbízhatóan.

**Fontos megállapítás:**

- a hiba nem kizárólag a saját monitor-config scriptben jelentkezik;
- a KDE gyári kijelzőbeállításai is ugyanazt a hibás elrendezést produkálják;
- a Soundbar kikapcsolása / kihúzása után, csak TV-vel is előfordul;
- X11 alatt is jelentkezik.

**Következtetés:** A probléma valószínűleg KDE/KScreen, EDID, HDMI/TV vagy driver oldali, nem az alkalmazáslogika hibája.

---

## Display-toggle.py

MS-DOS 6.22 stílusú, `curses`-alapú TUI vezérlőpult egy kapcsolódó, de önálló szolgáltatáshoz: a `edp-blank.service`-hez, ami a laptop belső kijelzőjének (eDP) háttérvilágítását sötétíti el inaktivitás esetén, **DPMS helyett** — így a USB-C-n futó Soundbar és a HDMI-n lógó TV videó/audio jele nem szakad meg, amikor a laptop panel elalszik.

A két eszköz (`monitor-config` és `display-toggle.py`) egymástól függetlenül működik, de ugyanahhoz a hardver-kombinációhoz (belső kijelző + Soundbar + TV) kapcsolódik, ezért kerültek egy repóba.

### Funkciók

- Nyílbillentyűs navigáció (`↑`/`↓` vagy `j`/`k`), `Enter` a választáshoz, gyorsgombok (`1`, `2`, `3`)
- Élő állapotjelzés a service jelenlegi futási állapotáról
- **Állapot részletesen** nézet, ami megmutatja:
  - Service állapot (ACTIVE / INACTIVE)
  - eDP panel állapota (Active / Blanked)
  - HDMI kimenet állapota (`xrandr` alapján)
  - Soundbar / audio sink állapota (`pactl` alapján, RUNNING esetén "Active (playing)")

### Menüpontok

```
1. Szolgáltatás Be   (automatikus kijelző elsötétítés idle esetén)
2. Szolgáltatás Ki   (csak erre a munkamenetre, loginnál újraindul)
3. Állapot részletesen
```

A "Ki" opció szándékosan **nem** `disable`-öl, csak `stop`-ol — így filmnézéshez/YouTube-hoz gyorsan kikapcsolható az automatikus elsötétítés, de a következő bejelentkezéskor a szolgáltatás magától újra aktív lesz.

### Függőségek

- Python 3 (`curses` a standard library része, nem kell külön telepíteni)
- `xrandr` (csomag: `x11-xserver-utils`)
- `pactl` (csomag: `pulseaudio-utils`, PipeWire alatt is működik a kompatibilitási réteg miatt)

### Használat

```bash
python3 display-toggle.py
```

Érdemes egy `.bashrc` alias mögé tenni:

```bash
alias display='python3 ~/.local/bin/display-toggle.py'
```

### Tervezett bővítések

- Időzített szüneteltetés (pl. "Kikapcsolás 2 órára", majd automatikus visszakapcsolás `systemd-run --user --on-active=...` segítségével)
- Film / YouTube / Zene mód, előre definiált profilokkal
- Folyamatfigyelés (pl. `mpv` vagy teljes képernyős böngésző ablak érzékelése) az automatikus mód-váltáshoz
- KDE értesítés (`notify-send`) állapotváltáskor
