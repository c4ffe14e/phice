from collections.abc import Callable
from typing import Any

from .lib.utils import get_setting


def types(obj: object) -> str:
    return type(obj).__name__


GLOBALS: dict[str, Callable[..., Any]] = {
    "type": types,
    "get_setting": get_setting,
}
