from collections.abc import Callable
from typing import Any

from .flask_utils import get_config, get_user_settings


def types(obj: object) -> str:
    return type(obj).__name__


GLOBALS: dict[str, Callable[..., Any]] = {
    "type": types,
    "get_config": get_config,
    "get_user_settings": get_user_settings,
}
