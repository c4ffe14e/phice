from flask import Blueprint, abort, render_template, request

from ..flask_utils import get_proxy
from ..lib.extractor import GetAlbum

bp: Blueprint = Blueprint("albums", __name__)


@bp.route("/media/set")
def albums() -> str:
    set_id: str | None = request.args.get("set")
    if not set_id:
        abort(400)

    album = GetAlbum(
        set_id,
        request.args.get("cursor"),
        proxy=get_proxy(),
    )

    return render_template(
        "album.html.jinja",
        album=album.album,
        cursor=album.cursor,
        has_next=album.has_next,
        title=album.album.title,
    )
