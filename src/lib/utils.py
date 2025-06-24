import base64
from contextlib import suppress
from typing import Any, cast
from urllib.parse import urlparse

from flask import current_app, request


def base64s(s: str) -> str:
    return base64.standard_b64encode(s.encode()).decode()


def base64s_decode(s: str) -> str:
    return base64.standard_b64decode(s.encode()).decode()


def urlbasename(url: str) -> str:
    return list(filter(None, urlparse(url).path.split("/")))[-1]


def nohostname(url: str) -> str:
    return urlparse(url)._replace(netloc="", scheme="").geturl()


def get_setting(name: str) -> str | None:
    defualt_value: str | None = None
    with suppress(KeyError):
        defualt_value = str(cast("Any", current_app.config["DEFAULT_SETTINGS"][name]))

    return request.cookies.get(name, defualt_value)
