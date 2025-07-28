from flask import Blueprint, abort, current_app, render_template, request

from ..flask_utils import get_proxy
from ..lib.extractor import get_group

bp: Blueprint = Blueprint("groups", __name__)


@bp.route("/groups/<string:token>")
def groups(token: str) -> str | tuple[str, dict[str, str]]:
    feed, scroll = get_group(token, request.args.get("cursor"), proxy=get_proxy())

    if request.args.get("rss"):
        if not current_app.config["ENABLE_RSS"]:
            abort(403, "RSS feeds are disabled in this instance")

        return render_template("timeline.rss.jinja", feed=feed), {"content-type": "application/rss+xml"}

    return render_template("timeline.html.jinja", feed=feed, scroll=scroll, title=feed.name)
