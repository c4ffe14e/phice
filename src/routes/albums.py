from flask import Blueprint, abort, render_template, request

from ..flask_utils import get_proxy
from ..lib.exceptions import InvalidResponse, NotFound, ResponseError
from ..lib.extractor import GetAlbum

bp: Blueprint = Blueprint("albums", __name__)


@bp.route("/media/set")
def albums() -> str:
    try:
        album = GetAlbum(request.args.get("set"), request.args.get("cursor"), proxy=get_proxy())
    except NotFound:
        abort(404, "Album not found")
    except (InvalidResponse, ResponseError) as e:
        abort(500, ", ".join(e.args))

    return render_template(
        "album.html.jinja",
        items=album.items,
        cursor=album.cursor,
        has_next=album.has_next,
        title=album.title,
    )
