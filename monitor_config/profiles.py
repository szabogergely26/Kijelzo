# -*- coding: utf-8 -*-
"""A gépfüggetlen KScreen profilok közös definíciói."""


PROFILE_LAPTOP = "Laptop (csak)"
PROFILE_LAPTOP_SOUNDBAR = "Laptop + Soundbar"
PROFILE_ALL = "Laptop + TV + Soundbar"


KSCREEN_PROFILES = {
    PROFILE_LAPTOP: {
        "enabled_roles": ("laptop",),
        "description": "Csak a laptop kijelző aktív.",
    },
    PROFILE_LAPTOP_SOUNDBAR: {
        "enabled_roles": ("laptop", "soundbar"),
        "description": "A laptop és a soundbar kijelző-ága aktív.",
    },
    PROFILE_ALL: {
        "enabled_roles": ("laptop", "tv", "soundbar"),
        "description": "A laptop, a TV és a soundbar kijelző-ága aktív.",
    },
}


PROFILE_ORDER = (
    PROFILE_LAPTOP,
    PROFILE_LAPTOP_SOUNDBAR,
    PROFILE_ALL,
)


DEFAULT_PROFILE = PROFILE_LAPTOP


def get_profile_names() -> list[str]:
    return list(PROFILE_ORDER)


def get_profile(profile_name: str):
    return KSCREEN_PROFILES.get(profile_name)


def get_default_profile_name() -> str:
    return DEFAULT_PROFILE


# Kompatibilitás a régebbi modulnevekkel; új kód már a fenti neveket használja.
X11_PROFILES = KSCREEN_PROFILES
DEFAULT_X11_PROFILE = DEFAULT_PROFILE
get_x11_profile_names = get_profile_names
get_x11_profile = get_profile
get_default_x11_profile_name = get_default_profile_name
