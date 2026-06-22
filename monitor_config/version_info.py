"""
Verzió- és kiadási csatorna információk a Monitor Config alkalmazáshoz.
"""


APP_NAME = "Monitor Config"

APP_VERSION = "0.1.0"

APP_CHANNEL = "dev"


def get_display_version() -> str:
    """
    Felhasználóbarát verziószöveg előállítása.
    """

    if APP_CHANNEL == "stable":
        return APP_VERSION

    if APP_CHANNEL == "preview":
        return f"{APP_VERSION} preview"

    if APP_CHANNEL == "dev":
        return f"{APP_VERSION} dev"

    return APP_VERSION