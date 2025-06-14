from flask import Blueprint, abort, render_template, request

from ..lib.exceptions import NotFound
from ..lib.extractor import GetAlbum

bp: Blueprint = Blueprint("albums", __name__)


@bp.route("/media/set")
def albums() -> str:
    try:
        album = GetAlbum(request.args.get("set"), request.args.get("cursor"))
    except NotFound:
        abort(404, "Album not found")

    return render_template(
        "album.html.jinja",
        items=album.items,
        cursor=album.cursor,
        has_next=album.has_next,
        title=album.title,
    )
