from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx
from flask import Blueprint, abort, redirect, render_template, request
from werkzeug import Response

from ..flask_utils import get_proxy
from ..lib.exceptions import InvalidResponse, NotFound, RateLimitError, ResponseError
from ..lib.extractor import GetPost
from ..lib.utils import nohostname
from ..lib.wrappers import http_client

bp: Blueprint = Blueprint("posts", __name__)


@bp.route("/<string:author>/posts/<string:token>", endpoint="posts")
@bp.route("/<string:author>/videos/<string:token>", endpoint="videos")
@bp.route("/reel/<string:token>", defaults={"author": ""}, endpoint="reel")
@bp.route("/groups/<string:author>/permalink/<string:token>", endpoint="groups_posts")
@bp.route("/groups/<string:author>/posts/<string:token>", endpoint="groups_posts")
@bp.route("/photo.php", defaults={"author": "", "token": ""}, endpoint="photo")
@bp.route("/photo", defaults={"author": "", "token": ""}, endpoint="photo")
@bp.route("/permalink.php", defaults={"author": "", "token": ""}, endpoint="permalink")
def posts(author: str, token: str) -> str:
    post = GetPost(
        request.args.get("cursor"),
        request.args.get("comment_id"),
        request.args.get("sort"),
        proxy=get_proxy(),
    )

    try:
        match request.endpoint:
            case "posts.videos":
                post.from_video(author, token)
            case "posts.reel":
                post.from_reel(token)
            case "posts.groups_posts":
                post.from_group_post(author, token)
            case "posts.photo":
                post.from_photo(request.args.get("fbid"))
            case "posts.permalink":
                post.from_post(request.args.get("id"), request.args.get("story_fbid"))
            case _:
                post.from_post(author, token)
    except NotFound:
        abort(404, "Post not found")
    except RateLimitError:
        abort(500, "Got rate-limited")
    except (InvalidResponse, ResponseError) as e:
        abort(500, ", ".join(e.args))

    if post.post is None:
        abort(500)

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
