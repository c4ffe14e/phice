import base64
from collections.abc import Generator, Mapping, MutableMapping
from contextlib import contextmanager
from types import UnionType
from typing import Any, is_typeddict
from typing import get_args as get_type_args
from urllib.parse import urlparse

from .api import API_ERROR_CODES
from .datatypes import Scroll
from .exceptions import ResponseError


def base64s(s: str) -> str:
    return base64.standard_b64encode(s.encode()).decode()


def base64s_decode(s: str) -> str:
    return base64.standard_b64decode(s.encode()).decode()


def urlbasename(url: str) -> str:
    return list(filter(None, urlparse(url).path.split("/")))[-1]


@contextmanager
def catch_rate_limit(obj: Scroll) -> Generator[None]:
    try:
        yield
    except ResponseError as e:
        if e.code != API_ERROR_CODES["rate_limit"]:
            raise
        obj.rate_limited = True
        obj.cursor = None
        obj.has_next = False


def dict_check_type(obj: object, d: Mapping[Any, Any]) -> None:
    for x, y in obj.__annotations__.items() - ((k, type(v)) for k, v in d.items()):
        if is_typeddict(y) and isinstance(d[x], dict):
            dict_check_type(y, d[x])
        elif x in d and type(y) is UnionType and type(d[x]) in get_type_args(y):
            continue
        else:
            raise TypeError(f"{x} has the wrong type")


def deep_merge(d: MutableMapping[Any, Any], dm: MutableMapping[Any, Any]) -> None:
    for k, v in dm.items():
        if isinstance(v, MutableMapping) and isinstance(d.get(k), MutableMapping):
            deep_merge(d[k], v)  # pyright: ignore[reportUnknownArgumentType]
        else:
            d[k] = v
