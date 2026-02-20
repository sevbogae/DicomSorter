from typing import Any

from toml import load, dump

from dicomsorter.controls.explorer import get_asset


# TODO: Change this to a more robust way of handling settings. Look into platformdirs or something similar.
#  Because the _MEIPASS directory is actually read-only and resets every time the application is restarted, we
#  need to save the settings to a different location.


def read_settings() -> dict[str, Any]:
    """Read settings from a TOML file."""
    try:
        return load(get_asset("assets/settings.toml"))
    except FileNotFoundError:
        return {}


def save_settings(settings: dict[str, Any]) -> None:
    """Save settings to a TOML file."""
    with open(get_asset("assets/settings.toml"), "w") as f:
        dump(settings, f)
