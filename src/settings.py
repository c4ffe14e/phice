from dataclasses import dataclass
from typing import Any, NewType, get_type_hints, override

from flask import has_request_context, request

Undefined = NewType("Undefined", object)


class ConfigBase:
    @override
    def __setattr__(self, name: str, value: Any, /) -> None:
        type_hints: dict[str, Any] = get_type_hints(self)
        if not (name in type_hints and isinstance(value, type_hints[name])):
            raise TypeError
        super().__setattr__(name, value)

    def type_check(self) -> None:
        for k, t in get_type_hints(self).items():
            if not isinstance(getattr(self, k), t):
                raise TypeError


@dataclass
class UserSettings(ConfigBase):
    theme: str = "default"
    comments_sort: str = "filtered"
    proxy: bool = True
    expand: bool = False
    timezone: int = 0

    @override
    def __getattribute__(self, name: str, /) -> Any:
        if has_request_context():
            v: Any | Undefined = request.cookies.get(name, Undefined)
            if v in ("on", "true"):
                v = True
            elif v in ("off", "false"):
                v = False
            elif isinstance(v, str) and v.isdigit():
                v = int(v)

            if v is not Undefined:
                return v
        return super().__getattribute__(name)


@dataclass
class PhiceConfig(ConfigBase):
    enable_rss: bool = True
    proxy: str | None = None
