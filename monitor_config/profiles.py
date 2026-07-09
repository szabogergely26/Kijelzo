# -*- coding: utf-8 -*-
"""
Monitor-config profil definíciók.

Fontos:
- Itt NINCS konkrét xrandr kimenetnév.
- Itt NINCS gépre égetett felbontás vagy pozíció.
- Ez a fájl csak azt írja le, hogy egy profil milyen kijelző-szerepeket akar használni.

A konkrét outputok, például:
    eDP
    HDMI-A-0
    DisplayPort-1
    HDMI-1-0
    DP-1-0

mind az aktuális / mentett xrandr kimenetből jönnek.
"""


# X11 profilok – gépfüggetlen profil-szándékok

X11_PROFILES = {
    "Laptop (csak)": {
        "enabled_roles": ["laptop"],
        "layout": "laptop_only",
        "description": "Csak a laptop kijelző aktív.",
    },

    "Laptop + Soundbar": {
        "enabled_roles": ["laptop", "soundbar"],
        "layout": "laptop_soundbar",
        "description": "Laptop + soundbar, TV kikapcsolva.",
    },

    "Laptop + TV + Soundbar": {
        "enabled_roles": ["laptop", "tv", "soundbar"],
        "layout": "tv_laptop_soundbar",
        "description": "TV fent, laptop alatta, soundbar aktív.",
    },
}


PROFILE_ORDER = [
    "Laptop (csak)",
    "Laptop + Soundbar",
    "Laptop + TV + Soundbar",
]


DEFAULT_X11_PROFILE = "Laptop (csak)"


def get_x11_profile_names():
    """Visszaadja a profilneveket a kívánt GUI-sorrendben."""
    return [name for name in PROFILE_ORDER if name in X11_PROFILES]


def get_x11_profile(profile_name):
    """Egy X11 profil definíciójának lekérése név alapján."""
    return X11_PROFILES.get(profile_name)


def get_default_x11_profile_name():
    """Alapértelmezett X11 profil neve."""
    return DEFAULT_X11_PROFILE
