from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx
from flask import Blueprint, abort, redirect, render_template, request
from werkzeug import Response

from ..flask_utils import get_proxy
from ..lib.exceptions import NotFound, ParsingError, ResponseError
from ..lib.extractor import GetPost
from ..lib.utils import nohostname
from ..lib.wrappers import http_client

bp: Blueprint = Blueprint("posts", __name__)


@bp.route("/<string:author>/posts/<string:token>", endpoint="posts")
@bp.route("/<string:author>/videos/<string:token>", endpoint="videos")
@bp.route("/reel/<string:token>", endpoint="reel")
@bp.route("/groups/<string:author>/permalink/<string:token>", endpoint="groups_posts")
@bp.route("/groups/<string:author>/posts/<string:token>", endpoint="groups_posts")
@bp.route("/photo.php", endpoint="photo")
@bp.route("/photo", endpoint="photo")
@bp.route("/permalink.php", endpoint="permalink")
@bp.route("/story.php", endpoint="story")
def posts(author: str = "", token: str = "") -> str:  # pyright: ignore[reportUnusedParameter] # noqa: ARG001
    try:
        post = GetPost(
            request.args.get("fbid", request.args.get("story_fbid", token)),
            request.args.get("cursor"),
            request.args.get("comment_id"),
            request.args.get("sort"),
            proxy=get_proxy(),
        )
    except NotFound:
        abort(404, "Post not found")
    except (ParsingError, ResponseError) as e:
        abort(500, ", ".join(e.args))

    return render_template(
        "post.html.jinja",
        post=post.post,
        comments=post.comments,
        cursor=post.cursor,
        has_next=post.has_next,
        title=post.post.text[:58],
    )


@bp.route("/watch")
def watch() -> Response:
    v: str | None = request.args.get("v")
    if not v:
        abort(400)

    with http_client(proxy=get_proxy()) as client:
        r: httpx.Response = client.get(
            "https://www.facebook.com/watch",
            params={"v": v},
            follow_redirects=False,
        )
    location: str | None = r.headers.get("location")

    if r.status_code != 302 or location is None:
        abort(404)

    return redirect(nohostname(location))
