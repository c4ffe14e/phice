from flask import Blueprint, abort, redirect
from flask.typing import ResponseReturnValue

from src.flask_utils import get_config

from ..lib.extractor import get_shared_url

bp: Blueprint = Blueprint("share", __name__)


@bp.route("/share/<path:path>")
def share(path: str) -> ResponseReturnValue:
    url: str | None = get_shared_url(path, get_config().proxy)
    if url is None:
        abort(404)

    return redirect(url)
