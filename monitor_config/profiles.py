# -*- coding: utf-8 -*-

# Lenovo LOQ – Debian KDE/X11/NVIDIA
#
# xrandr kimenetek:
#   eDP      = laptop kijelző
#   HDMI-1-0 = LG TV
#   DP-1-0   = Citation / Soundbar HDMI audio-kijelző

EDP_NAME = "eDP"
EDP_RES = "1920x1080"

HDMI_NAME = "HDMI-1-0"
HDMI_RES = "3840x2160"

SOUNDBAR_NAME = "DP-1-0"
SOUNDBAR_RES = "1920x1080"

DP2_NAME = SOUNDBAR_NAME

# LOQ teljes elrendezés:
#   DP-1-0     1920x1080+0+0
#   HDMI-1-0   3840x2160+0+254
#   eDP        1920x1080+966+2414
EDP_POS_SOLO = (0, 0)
EDP_POS_UNDER_TV = (966, 2414)
HDMI_POS = (0, 254)
SOUNDBAR_POS = (0, 0)


# X11 profilok – Lenovo LOQ

X11_PROFILES = {
    "Laptop (csak)": {
        "commands": [
            "xrandr --output DP-1-0 --off --output HDMI-1-0 --off",
            "sleep 0.5",
            "xrandr --fb 1920x1080 --output eDP --primary --mode 1920x1080 --rate 144.00 --pos 0x0",
        ],
        "description": "LOQ: csak a laptop kijelző aktív.",
    },

    "Laptop + Soundbar": {
        "commands": [
            "xrandr --output HDMI-1-0 --off",
            "sleep 0.5",
            "xrandr --fb 3840x1080 --output eDP --primary --mode 1920x1080 --rate 144.00 --pos 0x0 --output DP-1-0 --mode 1920x1080 --rate 59.94 --pos 1920x0",
        ],
        "description": "LOQ: laptop + soundbar, TV kikapcsolva.",
    },

    "Laptop + TV + Soundbar": {
        "commands": [
            "xrandr --fb 3840x3494 --output DP-1-0 --mode 1920x1080 --rate 59.94 --pos 0x0 --output HDMI-1-0 --mode 3840x2160 --rate 23.98 --pos 0x254 --output eDP --primary --mode 1920x1080 --rate 144.00 --pos 966x2414",
        ],
        "description": "LOQ: TV fent, laptop alatta, soundbar aktív.",
    },
}
