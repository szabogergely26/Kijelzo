# -*- coding: utf-8 -*-

APP_NAME = "Display Switcher"
APP_DISPLAY_NAME = "Kijelző beállítások"
APP_VERSION = "0.1.3"
APP_CHANNEL = "loq-local"


def get_window_title(dry_run: bool = False) -> str:
    title = APP_DISPLAY_NAME
    if dry_run:
        title += " — DRY RUN"
    return title
