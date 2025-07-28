from collections.abc import Callable
from typing import Any

from .flask_utils import GetUserSetting


def types(obj: object) -> str:
    return type(obj).__name__


GLOBALS: dict[str, Callable[..., Any]] = {
    "type": types,
    "GetUserSetting": GetUserSetting,
}
