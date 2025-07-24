import base64
from collections.abc import Generator
from contextlib import contextmanager
from urllib.parse import urlparse

from .api import API_ERROR_CODES
from .datatypes import Pageable
from .exceptions import ResponseError


def base64s(s: str) -> str:
    return base64.standard_b64encode(s.encode()).decode()


def base64s_decode(s: str) -> str:
    return base64.standard_b64decode(s.encode()).decode()


def urlbasename(url: str) -> str:
    return list(filter(None, urlparse(url).path.split("/")))[-1]


@contextmanager
def catch_rate_limit(obj: Pageable) -> Generator[None]:
    try:
        yield
    except ResponseError as e:
        if e.code != API_ERROR_CODES["rate_limit"]:
            raise
        obj.rate_limited = True
        obj.cursor = None
        obj.has_next = False
