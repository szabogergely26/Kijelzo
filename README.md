# Monitor-config / Kijelzőprofil-váltó
Részletesebb hibaleírás - Jegyzőkönyv: [changelog.md] (changelog.md)

A **Monitor-config** egy saját használatra készült, PyQt5-alapú kijelzőprofil-váltó KDE Plasma környezethez.

A program célja, hogy a laptop kijelzője, a TV és a Soundbar között gyorsan, biztonságosan és ismételhetően lehessen váltani anélkül, hogy minden alkalommal kézzel kellene `xrandr` vagy `kscreen-doctor` parancsokat futtatni.


## Változások

### 0.1.4 – 2026.08.01
- Javítva a hidegindítású HDMI/TV-profilváltásnál (kikapcsolt → bekapcsolt)
  jelentkező fekete képernyő (kurzorral): a `cli.py`
  `_restart_plasmashell_detached()` függvénye eddig egy locale-függő,
  hibásan tizedesvesszős `sleep 2,5` parancsot tartalmazott, ami más
  (pl. `C`) locale alatt azonnal hibával elszállt, így a plasmashell a
  HDMI stabilizálódása előtt indult újra. Helyette most `LC_ALL=C` és egy
  `kscreen-doctor -o` kimenetét figyelő poll-loop biztosítja, hogy a
  plasmashell csak a kijelzőállapot stabilizálódása után induljon újra
  (timeout-tal biztosítva a végtelen várakozás ellen). A plasmoidból
  (widgetből) indított profilváltás is érintett volt, javítva.

### 0.1.3 – 2026.07.20
- A `org.szaboger.kijelzovalto` plasmoid mostantól a `.deb` csomag része,
  nem kell külön kézzel telepíteni.







## Jelenlegi állapot

A program jelenleg használható, telepíthető alkalmazásként működik.

Támogatott munkamenetek:

- **X11** – `xrandr` használatával
- **Wayland** – `kscreen-doctor` használatával

A működés Lenovo ThinkPad és Lenovo LOQ gépen is tesztelve lett.  
A konkrét profilok és kimenetnevek gépenként eltérhetnek, ezért a program a kijelzők felismerését és a profilok alkalmazását külön kezeli.

## Fő funkciók

- kijelzőprofilok alkalmazása grafikus felületről;
- X11 és Wayland munkamenet felismerése;
- `xrandr`-alapú profilkezelés X11 alatt;
- `kscreen-doctor`-alapú profilkezelés Wayland alatt;
- laptop-, TV- és Soundbar-kimenetek kezelése;
- biztonságos hibakezelés hiányzó vagy ismeretlen kijelzőkiosztás esetén;
- naplózás hibakereséshez;
- biztonságos tesztmód a kijelzők tényleges átállítása nélkül;
- Debian-csomagból telepíthető alkalmazás;
- APT-szoftverforrásból frissíthető telepítés.

## Biztonságos működés

A program nem próbál meg bizonytalan kijelzőkiosztásra vakon parancsokat futtatni.

Fontos alapelv:

> Egy kijelzőt nem kapcsolunk be automatikusan csak azért, mert a rendszer `connected` állapotúnak jelzi.

Ez különösen fontos a Soundbar esetén, amely HDMI- vagy DisplayPort-eszközként kijelzőnek is látszhat, miközben elsődlegesen audioeszközként használjuk.

Ha a felismeréshez szükséges adatok hiányoznak vagy nem értelmezhetők, a program nem alkalmaz bizonytalan profilt.

## X11 működés

X11 alatt a program az `xrandr` parancsot használja.

A kijelzők felismerése történhet:

- élő `xrandr`-lekérdezésből;
- mentett `xrandr`-kimenetből.

A mentett felismerési fájl alapértelmezett helye:

```text
~/.config/monitor-config/xrandr-input.txt
```

Ez lehetővé teszi, hogy egy korábban elmentett kijelzőállapot alapján lehessen tesztelni a felismerést és a profilokat anélkül, hogy minden kijelzőt fizikailag újra csatlakoztatni kellene.

Példa mentésre:

```bash
mkdir -p ~/.config/monitor-config
xrandr --query > ~/.config/monitor-config/xrandr-input.txt
```

A fájl tartalma kézzel is bemásolható.

## Wayland működés

Wayland alatt a program a `kscreen-doctor` parancsot használja.

Az aktuális kijelzők és módok ellenőrzése:

```bash
kscreen-doctor -o
```

A program a Wayland-profilok alkalmazásakor az itt látható kimenetazonosítókat, módokat, pozíciókat és engedélyezési állapotokat használja.

## Profilok

A profilok gép- és kijelzőkiosztás-függők.

Tipikus profilok:

- csak laptop;
- laptop + Soundbar;
- laptop + TV + Soundbar.

A konkrét kimenetnevek például az alábbiak lehetnek:

### ThinkPad

```text
eDP-1
HDMI-A-0
DisplayPort-1
```

### Lenovo LOQ

```text
eDP
HDMI-1-0
DP-1-0
```

A program nem feltételezi, hogy minden gépen ugyanazok a kimenetnevek szerepelnek.

## Soundbar-kezelés

A Soundbar a Linux grafikus alrendszerében kijelzőként is megjelenhet, mert HDMI- vagy DisplayPort-kapcsolaton keresztül csatlakozik.

Ezért a programban a Soundbar:

- kijelzőkimenetként is kezelhető;
- audioútvonal része is lehet;
- géptől és kábelezéstől függően eltérő néven jelenhet meg.

Az audioátirányítás hardver- és PipeWire-konfigurációfüggő.  
A kijelzőprofilok működése és az audioeszköz kiválasztása külön hibaforrásként kezelendő.

## Biztonságos tesztmód

A program támogat olyan tesztmódot, amelyben kiírja és naplózza a futtatandó parancsokat, de nem módosítja ténylegesen a kijelzőbeállításokat.

Ez használható például:

```bash
monitor-config --dry
```

vagy a fejlesztői konfigurációban a `DRY_RUN` beállítással.

A tesztmód különösen hasznos új profilok, másik gép vagy új kijelzőkiosztás ellenőrzéséhez.

## Telepítés

A program Debian-alapú rendszeren `.deb` csomagból telepíthető.

Telepítés helyi csomagból:

```bash
sudo apt install ./monitor-config_*.deb
```

Telepítés után indítható:

```bash
monitor-config
```

A grafikus alkalmazás az alkalmazásmenüből is elérhető.

## APT-szoftverforrás

A telepített csomag tartalmazhatja a Monitor-config APT-szoftverforrásának beállítását is.

A forrás ellenőrzése:

```bash
sudo apt update
```

Ha a szoftverforrás helyesen van telepítve, az `apt update` kimenetében megjelenik a Monitor-config tárolója és az aktuális kiadási csatorna.

## Függőségek

Főbb futási függőségek:

```text
Python 3
PyQt5
xrandr
kscreen-doctor
```

Debian / KDE alatt szükséges csomagok például:

```bash
sudo apt install python3-pyqt5 x11-xserver-utils libkscreen-bin
```

Értesítésekhez és kapcsolódó integrációhoz szükség lehet még:

```bash
sudo apt install python3-gi gir1.2-notify-0.7 libnotify-bin
```

A pontos függőségeket a Debian-csomag vezérlőfájlja tartalmazza.

## Projektstruktúra

A projekt moduláris felépítést használ.

```text
Kijelzo/
├── main.py
├── monitor_config/
│   ├── app.py
│   ├── autodetect.py
│   ├── command_utils.py
│   ├── log_utils.py
│   ├── profiles.py
│   ├── version_info.py
│   └── xrandr_input.py
├── packaging/
│   └── deb/
├── README.md
└── .gitignore
```

A modulok fő feladatai:

- `main.py` – alkalmazásindítás;
- `app.py` – grafikus felület és vezérlés;
- `autodetect.py` – kijelzők felismerése;
- `xrandr_input.py` – élő vagy mentett `xrandr`-adatok kezelése;
- `profiles.py` – kijelzőprofilok és parancsok;
- `command_utils.py` – külső parancsok biztonságos futtatása;
- `log_utils.py` – naplózás;
- `version_info.py` – verzió- és csatornaadatok.

## Naplózás

A program működése naplófájlban követhető.

A pontos naplóútvonalat a program Névjegy ablaka vagy az indulási kimenet jelzi.

Élő megfigyeléshez:

```bash
tail -f /naplo/pontos/eleresi/utja
```

A napló többek között tartalmazhatja:

- az észlelt munkamenetet;
- a felismerés forrását;
- a csatlakoztatott kimeneteket;
- a kiválasztott profilt;
- a futtatott vagy tesztmódban csak kiírt parancsokat;
- az esetleges hibákat.

## Hibakeresés

Elsőként az alábbi parancsok kimenetét érdemes ellenőrizni.

### X11

```bash
echo "$XDG_SESSION_TYPE"
xrandr --query
```

### Wayland

```bash
echo "$XDG_SESSION_TYPE"
kscreen-doctor -o
```

### Programindítás terminálból

```bash
monitor-config
```

Így az indulás közben keletkező hibák közvetlenül is láthatók.

## Fejlesztési irányok

Tervezett vagy lehetséges további fejlesztések:

- további gép- és kijelzőprofilok;
- profilok külső konfigurációs fájlba szervezése;
- parancssori profilalkalmazás;
- `--status`, `--version`, `--about` és diagnosztikai kapcsolók;
- modernebb grafikus felület;
- egyszerűbb egyéni profilkészítés;
- stabilabb és külön kezelhető audioprofilok.

## Megjegyzés

A projekt saját hardverkörnyezethez készült, ezért más gépen a profilok és kimenetnevek módosítására lehet szükség.

Új gépen vagy új kijelzőkiosztással először mindig a biztonságos tesztmód használata javasolt.
