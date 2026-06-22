#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys

from PyQt5.QtWidgets import QApplication

from monitor_config.app import MonitorSetupApp
from monitor_config.notifications import init_notifications
from monitor_config.version_info import APP_NAME


def main() -> int:
    qt_app = QApplication(sys.argv)

    init_notifications(APP_NAME)

    window = MonitorSetupApp()
    window.show()

    return qt_app.exec_()


if __name__ == "__main__":
    sys.exit(main())