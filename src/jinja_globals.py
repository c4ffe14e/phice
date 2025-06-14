from collections.abc import Callable
from typing import Any


def types(obj: object) -> str:
    return type(obj).__name__


GLOBALS: dict[str, Callable[..., Any]] = {
    "type": types,
}
