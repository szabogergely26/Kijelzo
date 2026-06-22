"""
Futási konfigurációk a Monitor Config alkalmazáshoz.
"""

import sys


# -- DRY RUN: ha --dry paraméterrel indítod, csak logolunk, nem futtatunk parancsot
DRY_RUN = "--dry" in sys.argv