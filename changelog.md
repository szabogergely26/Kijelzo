# Changelog

Ez a fájl a projektben előforduló nehezebben visszakereshető hibákat,
azok okát és a javításukat gyűjti, dátum szerint, hogy később (vagy más
projektben hasonló tünet esetén) gyorsan visszakereshető legyen.




## 2026-08-03

### Hiba: profilváltás után a teljes KDE felület angolra váltott

**Tünet:** Kijelző-profil váltás (pl. "Film / sorozat mód") után, amikor a
plasmashell automatikusan újraindult, a teljes Plasma felület (System
Settings, alkalmazásmenü, widgetek) angolra váltott, miközben minden
locale-beállítás (`~/.config/plasma-localerc`, `LANG` env, `systemctl
--user show-environment`) helyesen `hu_HU.UTF-8`-at mutatott. A jelenség a
GUI-ból indított profilváltásnál nem jelentkezett, csak a plasmoidból.
Egy teljesen friss bejelentkezés (logout/login) mindig visszaállította a
magyar felületet — egészen a következő plasmoidból indított profilváltásig.

**Ok:** A `cli.py`-ban a `_restart_plasmashell_detached()` egy `bash -c`
scriptet indít, ami a `kscreen-doctor -o` és a `sleep N,N` alakú
tizedesvesszős várakozás locale-függetlenítése miatt a script elején
`export LC_ALL=C`-t állít be. Ez a shell-en belül helyénvaló és szükséges
— viszont a script a végén ugyanebből a (már `LC_ALL=C`-vel szennyezett)
shell-ből indította el a `kstart5`/`kstart6 plasmashell`-t is. A `kstart`
nem tisztítja meg az örökölt környezetet, így az új plasmashell process
már explicit `LC_ALL=C`-vel indult el, és onnantól minden, amit a
plasmashell maga indított (Konsole, menük, System Settings), ezt a
környezetet örökölte tovább — egészen a következő teljes
kijelentkezésig/bejelentkezésig, ami friss (nem a plasmashell-ből
öröklött) környezettel indította újra a session-t.

**Hibakeresés menete (röviden):** `LANG` és `plasma-localerc` rendben
→ `systemctl --user show-environment` is rendben → a futó `plasmashell`
process `/proc/<pid>/environ`-jában viszont már `LC_ALL=C` szerepelt →
plasmashell manuális restart nem oldotta meg (mert ugyanabból a
szennyezett shell-ből indítottuk újra) → friss logout/login viszont
igen (tiszta env-vel indul a session) → ez megerősítette, hogy valami
*aktívan* exportálja és továbbadja ezt a beállítást minden alkalommal,
amikor a plasmashell újraindul → a `cli.py`-ban lévő `export LC_ALL=C;`
sor és a hozzá tartozó kommentek (amik már eleve utaltak a locale-függő
`sleep` viselkedésre) mutatták meg a pontos forrást.

**Javítás:** A `kstart5`/`kstart6` hívás elé egy eseti (csak arra az egy
parancsra vonatkozó) környezeti változó felülírás került, hogy a
`plasmashell` már helyes locale-lal induljon újra, függetlenül attól,
hogy az őt indító bash script korábbi lépései (`sleep`, `kscreen-doctor`
parse-olás) miért igényeltek `C` locale-t:

```bash
# előtte:
kstart5 plasmashell || kstart6 plasmashell;

# utána:
LC_ALL= LANG=hu_HU.UTF-8 kstart5 plasmashell || LC_ALL= LANG=hu_HU.UTF-8 kstart6 plasmashell;
```

**Tanulság:** Ha egy script a saját belső logikájának kiszámíthatósága
miatt (pl. `sleep N,N` vagy egy CLI-eszköz locale-függő kimenete miatt)
explicit `LC_ALL=C`-t (vagy bármilyen más env felülírást) állít be, és a
script a végén egy hosszú életű, más folyamatokat is indító processt
indít el (mint egy desktop shell), mindig érdemes explicit visszaállítani
vagy felülírni a környezetet közvetlenül az adott hívás előtt — különben
a "belső" env-hack kiszivároghat olyan folyamatokba is, amik jóval túlélik
magát a scriptet.






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


