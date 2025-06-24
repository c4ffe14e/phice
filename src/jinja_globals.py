from collections.abc import Callable
from typing import Any

from .flask_utils import GetSetting


def types(obj: object) -> str:
    return type(obj).__name__


GLOBALS: dict[str, Callable[..., Any]] = {
    "type": types,
    "GetSetting": GetSetting,
}
