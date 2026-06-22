#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys

from PyQt5.QtWidgets import QApplication

from monitor_config import app as app_module
from monitor_config.app import MonitorSetupApp, _HAS_GI_NOTIFY, APP_NAME


def main() -> int:
    qt_app = QApplication(sys.argv)

    if _HAS_GI_NOTIFY:
        try:
            app_module.Notify.init(APP_NAME)
        except Exception:
            pass

    window = MonitorSetupApp()
    window.show()

    return qt_app.exec_()


if __name__ == "__main__":
    sys.exit(main())