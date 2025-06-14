from flask import Blueprint, abort, current_app, render_template, request

from ..lib.exceptions import NotFound
from ..lib.extractor import GetProfile

bp: Blueprint = Blueprint("profile", __name__)


@bp.route("/profile.php", endpoint="php")
@bp.route("/people/<string:_>/<string:username>")
@bp.route("/<string:username>")
def profile(username: str = "", _: str | None = None) -> str | tuple[str, dict[str, str]]:
    token: str = request.args.get("id", "") if request.endpoint == "php" else username

    try:
        profile = GetProfile(token, request.args.get("cursor"))
    except NotFound:
        abort(404, f"{username} not found")

    if request.args.get("rss"):
        if not current_app.config["ENABLE_RSS"]:
            abort(403, "RSS feeds are disabled in this instance")

        return render_template(
            "timeline.rss.jinja",
            info=profile.feed,
            posts=profile.posts,
        ), {"content-type": "application/rss+xml"}

    return render_template(
        "timeline.html.jinja",
        info=profile.feed,
        posts=profile.posts,
        cursor=profile.cursor,
        has_next=profile.has_next,
        title=profile.feed.name,
    )
