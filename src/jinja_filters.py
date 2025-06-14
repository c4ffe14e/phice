import re
from collections.abc import Callable
from datetime import UTC, datetime
from typing import cast

from flask import current_app, request, url_for


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


def format_time_utc(timestamp: str | float) -> str:
    return datetime.fromtimestamp(float(timestamp), tz=UTC).strftime("%Y/%m/%d - %I:%M:%S %p UTC")


def format_time_rfc822(timestamp: str | float) -> str:
    return datetime.fromtimestamp(float(timestamp), tz=UTC).strftime("%a, %d %b %Y %H:%M:%S GMT")


def format_number(number: int) -> str:
    return f"{number:,}"


def proxy(s: str) -> str:
    if request.cookies.get("proxy", cast("str", current_app.config["DEFAULT_SETTINGS"]["proxy"])) != "on":
        return s
    return re.sub(r"https?://[^/]*.fbcdn.net/([^ ]*)", rf"{url_for('cdn.cdn', path='', _external=True)}\1", s)


FILTERS: dict[str, Callable[..., str]] = {
    "format_time": format_time,
    "format_time_utc": format_time_utc,
    "format_time_rfc822": format_time_rfc822,
    "format_number": format_number,
    "proxy": proxy,
}
