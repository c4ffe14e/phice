import re
from collections.abc import Callable
from datetime import UTC, datetime
from urllib.parse import ParseResult, urlparse

from flask import url_for

from .flask_utils import get_user_settings


def _proxy_sub(m: re.Match[str]) -> str:
    url: ParseResult = urlparse(m.group(0))

    endpoint: str = "cdn.cdn"
    if url.hostname and url.hostname.startswith("external."):
        endpoint = "cdn.cdn_external"

    return f"{url_for(endpoint, path=url.path[1:], _external=True)}?{url.query}"


def proxy(s: str) -> str:
    if get_user_settings().proxy:
        return re.sub(r"https?://[^/]*.fbcdn.net/[^ ]*", _proxy_sub, s)
    return s


def format_time(timestamp: str | float) -> str:
    time: datetime = datetime.fromtimestamp(float(timestamp))
    today: datetime = datetime.now()
    seconds: float = (today - time).total_seconds()

    if (since := int(seconds)) < 60:
        return f"{since} seconds ago"
    if (since := int(seconds / 60)) < 60:
        return f"{since} minutes ago"
    if (since := int(seconds / 60 / 60)) < 24:
        return f"{since} hours ago"
    if seconds / 60 / 60 / 24 < 1:
        return "Yestarday"
    if (since := int(seconds / 60 / 60 / 24)) < 7:
        return f"{since} days ago"
    if (since := int(seconds / 60 / 60 / 24 / 7)) < 4:
        return f"{since} weeks ago"
    if (today - time).days < 365:
        return time.strftime("%m/%d")
    return time.strftime("%Y/%m/%d")


def format_time_full(timestamp: str | float) -> str:
    time: float = float(timestamp)
    offset: int = get_user_settings().timezone
    time += offset * 60 * 60

    return datetime.fromtimestamp(time, tz=UTC).strftime(f"%Y/%m/%d - %I:%M:%S %p UTC{offset:+}")


def format_time_rfc822(timestamp: str | float) -> str:
    return datetime.fromtimestamp(float(timestamp), tz=UTC).strftime("%a, %d %b %Y %H:%M:%S GMT")


def format_number(number: int) -> str:
    return f"{number:,}"


FILTERS: dict[str, Callable[..., str]] = {
    "format_time": format_time,
    "format_time_full": format_time_full,
    "format_time_rfc822": format_time_rfc822,
    "format_number": format_number,
    "proxy": proxy,
}
