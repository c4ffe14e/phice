import httpx
from flask import Blueprint, abort, redirect
from werkzeug import Response

from src.lib.utils import nohostname

bp: Blueprint = Blueprint("share", __name__)


@bp.route("/share/<path:path>")
def share(path: str) -> Response:
    r = httpx.get(f"https://www.facebook.com/share/{path}")
    if r.status_code != 302:
        abort(404)

    return redirect(nohostname(r.headers["location"]))
