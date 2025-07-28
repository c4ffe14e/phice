from flask import Blueprint, abort, current_app, render_template, request

from ..flask_utils import get_proxy
from ..lib.extractor import get_profile

bp: Blueprint = Blueprint("profile", __name__)


@bp.route("/profile.php", endpoint="profile_php")
@bp.route("/people/<string:_>/<string:username>")
@bp.route("/<string:username>")
def profile(username: str = "", _: str | None = None) -> str | tuple[str, dict[str, str]]:
    token: str | None = request.args.get("id") if request.endpoint == "profile.profile_php" else username
    if not token:
        abort(400)

    feed, scroll = get_profile(token, request.args.get("cursor"), proxy=get_proxy())

    if request.args.get("rss"):
        if not current_app.config["ENABLE_RSS"]:
            abort(403, "RSS feeds are disabled in this instance")

        return render_template("timeline.rss.jinja", feed=feed), {"content-type": "application/rss+xml"}

    return render_template("timeline.html.jinja", feed=feed, scroll=scroll, title=feed.name)
