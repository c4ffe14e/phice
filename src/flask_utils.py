from contextlib import suppress
from typing import Any, cast

from flask import current_app, request


class GetSetting:
    def __init__(self, name: str) -> None:
        defualt_value: Any = None
        with suppress(KeyError):
            defualt_value = cast("Any", current_app.config["DEFAULT_SETTINGS"][name])
        self.__value: Any = request.cookies.get(name, defualt_value)

    def as_bool(self) -> bool:
        match self.__value:
            case True | 1 | "on" | "true":
                return True
            case False | 0 | "off" | "false":
                return False
            case _:
                return False

    def as_str(self) -> str:
        return str(self.__value)

    def as_int(self) -> int:
        ret: int = 0
        with suppress(ValueError):
            ret = int(self.__value)

        return ret


def get_proxy() -> str | None:
    try:
        ret: Any = cast("Any", current_app.config["NETWORK"]["proxy"])
        if ret is None or ret == "":
            return None
        return str(ret)
    except KeyError:
        return None
