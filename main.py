#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys


def main() -> int:
    if "--status" in sys.argv:
        from monitor_config.cli import print_current_status

        return print_current_status()

    if "--restart-shell" in sys.argv:
        from monitor_config.cli import restart_shell_headless

        return restart_shell_headless()

    if "--apply" in sys.argv:
        idx = sys.argv.index("--apply")
        try:
            profile_name = sys.argv[idx + 1]
        except IndexError:
            print('Használat: main.py --apply "<profil név>"', file=sys.stderr)
            return 2

        from monitor_config.cli import apply_profile_headless

        return apply_profile_headless(profile_name)

    from monitor_config.app import main as gui_main

    gui_main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
