from typing import Any

from toml import load, dump

from dicomsorter.controls.explorer import get_asset


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


if __name__ == "__main__":
    settings = read_settings()
    print(settings)
