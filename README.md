# Monitor-config / Kijelzőprofil-váltó

Részletesebb hibaleírás - Napló: [changelog.md](changelog.md)

A **Monitor-config** egy saját használatra készült, PyQt5-alapú kijelzőprofil-váltó KDE Plasma környezethez.

A program célja, hogy a laptop kijelzője, a TV és a Soundbar között gyorsan, biztonságosan és ismételhetően lehessen váltani anélkül, hogy minden alkalommal kézzel kellene `kscreen-doctor` parancsokat futtatni.

## A Változásokat és leírásukat a [changelog](changelog.md) tartalmazza

> **Megjegyzés az AI-közreműködésről:** A kód nagy része AI (Claude) segítségével
> készült, emberi tervezés, irányítás és folyamatos ellenőrzés mellett. A
> funkcionalitásért és a projekt irányáért a szerző felel.

## Jelenlegi állapot

A program jelenleg használható, telepíthető alkalmazásként működik.

A profilváltás kizárólag a KDE **KScreen** alrendszerén (`kscreen-doctor`) keresztül
történik. Ez X11 és Wayland munkamenet alatt is elérhető KDE Plasma alatt, ezért a
programnak nem kell külön ágon kezelnie a két munkamenet-típust — csak az fontos, hogy
`kscreen-doctor` elérhető legyen.

A működés Lenovo ThinkPad és Lenovo LOQ gépen is tesztelve lett. A konkrét kimenetnevek
gépenként eltérhetnek, de ez nem számít: a program a kimeneteket **nem névből**, hanem a
**csatlakoztatott kijelző szerepéből** (laptop-panel / legnagyobb felbontású külső = TV /
kisebb felbontású külső = Soundbar) ismeri fel élőben, minden alkalommal.

> **Gépek közötti eltérés:** eredetileg egy közös kódbázis lett volna mindkét gépen
> (LOQ és ThinkPad), de ez a gyakorlatban nem vált be maradéktalanul (pl. eltérő
> hardveres sajátosságok, kábelezés). Emiatt jelenleg gépenként külön git ág tartja a
> saját finomhangolásokat: a `master`/`main` ág a LOQ-n futó verzió, a
> `Lenovo-ThinkPad` ág a ThinkPad-re szabott verzió. A gépfüggetlen fő logika
> (kimenetfelismerés, profilszámítás) mindkét ágon közös marad, csak a gép-specifikus
> apró eltérések (pl. `APP_CHANNEL`) térnek el áganként.

## Fő funkciók

- kijelzőprofilok alkalmazása grafikus felületről;
- kimenetek felismerése a csatlakoztatott kijelző szerepe (laptop/TV/soundbar) alapján,
  a kimenet nevétől függetlenül;
- `kscreen-doctor`-alapú profilkezelés (X11 és Wayland alatt egyaránt);
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

## KScreen működés

A program minden támogatott munkamenetben a `kscreen-doctor` parancsot használja, X11
alatt is (a KDE Plasma X11-en is biztosítja a KScreen-backendet, nem csak Wayland alatt).

A kijelzők felismerése történhet:

- élő `kscreen-doctor -o`-lekérdezésből (elsődleges, minden alkalommal ez fut le előbb);
- mentett `kscreen-doctor -o`-kimenetből (csak akkor, ha az élő azonosítás nem
  egyértelmű, pl. a laptop-panel nem ismerhető fel egyértelműen).

A mentett felismerési fájl alapértelmezett helye:

```text
~/.config/monitor-config/kscreen-input.txt
```

Ez lehetővé teszi, hogy egy korábban elmentett kijelzőállapot alapján lehessen tesztelni a felismerést és a profilokat anélkül, hogy minden kijelzőt fizikailag újra csatlakoztatni kellene.

Példa mentésre:

```bash
mkdir -p ~/.config/monitor-config
kscreen-doctor -o > ~/.config/monitor-config/kscreen-input.txt
```

A fájl tartalma kézzel is bemásolható — a GUI "Kijelzők újrafelvétele" gombja is ezt segíti.

## Profilok

A profilok szerep-alapúak (laptop / TV / soundbar), nem konkrét kimenetnévhez kötöttek —
a program minden profilváltáskor élőben állapítja meg, melyik kimenet melyik szerepet
tölti be az adott gépen és pillanatban.

Tipikus profilok:

- csak laptop;
- laptop + Soundbar;
- laptop + TV + Soundbar.

A konkrét kimenetnevek gépenként eltérhetnek, például:

### ThinkPad

```text
eDP
HDMI-A-0
DisplayPort-1
```

### Lenovo LOQ

```text
eDP
HDMI-1-0
DP-1-0
```

Ezek csak illusztrációk — a program nem feltételezi, hogy egy adott gépen mindig ugyanaz a kimenetnév-készlet, és nem is ezekre a nevekre van "hardwire"-olva.

## Soundbar-kezelés

A Soundbar a Linux grafikus alrendszerében kijelzőként is megjelenhet, mert HDMI- vagy DisplayPort-kapcsolaton keresztül csatlakozik.

Ezért a programban a Soundbar:

- kijelzőkimenetként is kezelhető;
- audioútvonal része is lehet;
- géptől és kábelezéstől függően eltérő néven jelenhet meg.

Az audioátirányítás hardver- és PipeWire-konfigurációfüggő.  
A kijelzőprofilok működése és az audioeszköz kiválasztása külön hibaforrásként kezelendő.

## Biztonságos tesztmód

A program támogat olyan tesztmódot, amelyben kiírja és naplózza a futtatandó parancsokat, de nem módosítja ténylegesen a kijelzőbeállításokat — és a profilváltás utáni plasmashell-újraindítást sem futtatja le ténylegesen, csak logolja.

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
kscreen-doctor
```

Debian / KDE alatt szükséges csomagok például:

```bash
sudo apt install python3-pyqt5 libkscreen-bin
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
│   ├── cli.py
│   ├── command_utils.py
│   ├── config.py
│   ├── kscreen_input.py
│   ├── log_utils.py
│   ├── notifications.py
│   ├── profiles.py
│   ├── setup_dialog.py
│   └── version_info.py
├── packaging/
│   └── deb/
├── README.md
└── .gitignore
```

A modulok fő feladatai:

- `main.py` – alkalmazásindítás és parancssori kapcsolók (`--status`, `--apply`, `--restart-shell`);
- `app.py` – grafikus felület, kimenetfelismerés és profilszámítás (`build_kscreen_command`);
- `autodetect.py` – aktuális profil megállapítása egy felismert kijelző-kiosztásból;
- `kscreen_input.py` – élő vagy mentett `kscreen-doctor -o` kimenet strukturált feldolgozása;
- `cli.py` – fejnélküli (headless) profilváltás és asztal-helyreállítás parancssorból;
- `profiles.py` – kijelzőprofilok gépfüggetlen definíciói (szerep-alapú);
- `command_utils.py` – külső parancsok biztonságos futtatása;
- `notifications.py` – asztali értesítések (libnotify/KNotification);
- `setup_dialog.py` – első kijelzőfelvételt segítő párbeszédablak;
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

Elsőként az alábbi parancs kimenetét érdemes ellenőrizni — ez X11 és Wayland munkamenet alatt egyaránt ugyanaz:

```bash
kscreen-doctor -o
```

A munkamenet típusa (`echo "$XDG_SESSION_TYPE"`) csak tájékoztató jellegű, a program viselkedését nem befolyásolja.

Programindítás terminálból:

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

A projekt saját hardverkörnyezethez készült, ezért más gépen a profilok és kimenetnevek módosítására lehet szükség — bár a szerep-alapú felismerés miatt ez a legtöbb esetben magától is működik.

Új gépen vagy új kijelzőkiosztással először mindig a biztonságos tesztmód használata javasolt.
