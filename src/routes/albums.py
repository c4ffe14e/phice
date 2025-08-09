from flask import Blueprint, abort, render_template, request
from flask.typing import ResponseReturnValue

from src.flask_utils import get_config

from ..lib.extractor import get_album

bp: Blueprint = Blueprint("albums", __name__)


@bp.route("/media/set")
def albums() -> ResponseReturnValue:
    token: str | None = request.args.get("set")
    if not token:
        abort(400)

    album, scroll = get_album(token, request.args.get("cursor"), proxy=get_config().proxy)

    return render_template("albums.html.jinja", album=album, scroll=scroll, title=album.title)
