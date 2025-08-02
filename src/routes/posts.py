from flask import Blueprint, abort, render_template, request
from flask.typing import ResponseReturnValue

from ..flask_utils import UserSetting, get_proxy
from ..lib.extractor import get_post

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
@bp.route("/watch", endpoint="watch")
def posts(author: str | None = None, token: str | None = None) -> ResponseReturnValue:  # pyright: ignore[reportUnusedParameter] # noqa: ARG001
    post_id: str | None = None
    match request.endpoint:
        case "posts.photo":
            post_id = request.args.get("fbid")
        case "posts.permalink" | "posts.story":
            post_id = request.args.get("story_fbid")
        case "posts.watch":
            post_id = request.args.get("v")
        case _:
            post_id = token
    if not post_id:
        abort(400)

    post, scroll = get_post(
        post_id,
        request.args.get("cursor"),
        request.args.get("comment_id"),
        request.args.get("sort", str(UserSetting("comments_sort"))),
        proxy=get_proxy(),
    )

    return render_template("posts.html.jinja", post=post, scroll=scroll, title=post.text[:58])
