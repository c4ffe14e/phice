from contextlib import suppress
from typing import Any, cast, override

from flask import current_app, request


class UserSetting:
    def __init__(self, name: str) -> None:
        defualt_value: Any = None
        with suppress(KeyError):
            defualt_value = cast("Any", current_app.config["DEFAULT_SETTINGS"][name])

        self._value: Any = request.cookies.get(name, defualt_value)

    @override
    def __str__(self) -> str:
        return str(self._value)

    def __int__(self) -> int:
        ret: int = 0
        with suppress(ValueError):
            ret = int(self._value)

        return ret

    def __bool__(self) -> bool:
        match self._value:
            case True | 1 | "on" | "true" | "True":
                return True
            case _:
                return False

    @override
    def __eq__(self, value: object, /) -> bool:
        match value:
            case str():
                return str(self) == value
            case int():
                return int(self) == value
            case bool():
                return bool(self) == value
            case _:
                return False

    @override
    def __hash__(self) -> int:
        return hash(self._value)


def get_proxy() -> str | None:
    try:
        ret: Any = cast("Any", current_app.config["PROXY"])
    except KeyError:
        return None
    if not ret:
        return None
    return str(ret)
