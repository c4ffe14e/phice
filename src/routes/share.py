from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx
from flask import Blueprint, abort, redirect
from werkzeug import Response

from src.lib.utils import nohostname

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

    return redirect(nohostname(location))
