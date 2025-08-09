from flask import Blueprint, abort, render_template, request
from flask.typing import ResponseReturnValue

from ..flask_utils import get_config
from ..lib.extractor import get_profile

bp: Blueprint = Blueprint("profile", __name__)


@bp.route("/profile.php", endpoint="profile_php")
@bp.route("/people/<string:_>/<string:username>")
@bp.route("/<string:username>")
def profile(username: str = "", _: str | None = None) -> ResponseReturnValue:
    token: str | None = request.args.get("id") if request.endpoint == "profile.profile_php" else username
    if not token:
        abort(400)
    if request.args.get("rss") and not get_config().enable_rss:
        abort(403, "RSS feeds are disabled in this instance")

    feed, scroll = get_profile(token, request.args.get("cursor"), proxy=get_config().proxy)

    if request.args.get("rss"):
        return render_template("timeline.rss.jinja", feed=feed), {"content-type": "application/rss+xml"}
    return render_template("timeline.html.jinja", feed=feed, scroll=scroll, title=feed.name)
