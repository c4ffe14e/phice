from contextlib import suppress
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx
from urllib.parse import ParseResult, parse_qs, urlencode, urlparse

from flask import Blueprint, abort, redirect
from werkzeug import Response

from ..flask_utils import get_proxy
from ..lib.wrappers import http_client

bp: Blueprint = Blueprint("share", __name__)


@bp.route("/share/<path:path>")
def share(path: str) -> Response:
    with http_client(proxy=get_proxy()) as client:
        r: httpx.Response = client.get(
            f"https://www.facebook.com/share/{path}",
            follow_redirects=False,
        )

    location: str | None = r.headers.get("location")
    if r.status_code != 302 or location is None:
        abort(404)
    url: ParseResult = urlparse(location)
    query: dict[str, list[str]] = parse_qs(url.query)

    with suppress(KeyError):
        del query["rdid"]
        del query["share_url"]

    url = url._replace(
        netloc="",
        scheme="",
        query=urlencode(query, doseq=True),
    )

    return redirect(url.geturl())
