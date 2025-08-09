from typing import Any

from .flask_utils import get_config, get_user_settings


def types(obj: object) -> str:
    return type(obj).__name__


THEMES: dict[str, str] = {
    "default": "Default",
    "light": "Light",
    "black": "Black",
    "catppuccin_mocha": "Catppuccin mocha",
    "catppuccin_latte": "Catppuccin latte",
}

GLOBALS: dict[str, Any] = {
    "type": types,
    "get_config": get_config,
    "get_user_settings": get_user_settings,
    "THEMES": THEMES,
}
