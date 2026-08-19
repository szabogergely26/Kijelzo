# -*- coding: utf-8 -*-

APP_NAME = "Display Switcher"
APP_DISPLAY_NAME = "Kijelző beállítások"

# Verziószámozás: főverzió.kisebb-funkció.javítás (pl. 1.1.4)
#   1. szám (főverzió) - nagy, esetleg nem visszafelé kompatibilis változás;
#   2. szám (kisebb funkció) - új, visszafelé kompatibilis funkció/bővítés;
#   3. szám (javítás) - hibajavítás, funkcióbővítés nélkül.
APP_VERSION = "0.1.5"
APP_CHANNEL = "thinkpad-local"


def get_window_title(dry_run: bool = False) -> str:
    title = APP_DISPLAY_NAME
    if dry_run:
        title += " — DRY RUN"
    return title
