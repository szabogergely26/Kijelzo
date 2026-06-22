


"""
Kijelzőprofilok definíciói a Monitor Config alkalmazáshoz.
"""

# X11 profilok:

X11_PROFILES = {
    "Laptop (csak)": {
        "commands": [
            "xrandr --output HDMI-A-0 --off --output DisplayPort-1 --off",
            "sleep 0.5",
            "xrandr --output eDP --primary --mode 1920x1200 --pos 0x0",
        ],
        "description": "Csak a laptop kijelző aktív.",
    },

    "Laptop + Soundbar": {
        "commands": [
            "xrandr --output HDMI-A-0 --off",
            "sleep 0.5",
            "xrandr --output eDP --primary --mode 1920x1200 --pos 0x0",
            "sleep 0.5",
            "xrandr --output DisplayPort-1 --mode 1280x720 --same-as eDP",
        ],
        "description": "Laptop + Soundbar, a soundbar a laptop kijelzőt tükrözi.",
    },

    "Laptop + TV + Soundbar": {
        "commands": [
            "xrandr --output HDMI-A-0 --mode 3840x2160 --rate 60 --pos 0x0",
            "sleep 0.5",
            "xrandr --output eDP --primary --mode 1920x1200 --pos 960x2160",
            "sleep 0.5",
            "xrandr --output DisplayPort-1 --mode 1280x720 --same-as eDP",
        ],
        "description": "TV felül, laptop alul középen, soundbar a laptop kijelzőt tükrözi.",
    },
}