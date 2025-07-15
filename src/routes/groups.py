from flask import Blueprint, abort, current_app, render_template, request

from ..flask_utils import get_proxy
from ..lib.extractor import GetGroup

bp: Blueprint = Blueprint("groups", __name__)


@bp.route("/groups/<string:token>")
def groups(token: str) -> str | tuple[str, dict[str, str]]:
    group = GetGroup(token, request.args.get("cursor"), proxy=get_proxy())

    if request.args.get("rss"):
        if not current_app.config["ENABLE_RSS"]:
            abort(403, "RSS feeds are disabled in this instance")

        return render_template(
            "timeline.rss.jinja",
            info=group.feed,
            posts=group.posts,
        ), {"content-type": "application/rss+xml"}

    return render_template(
        "timeline.html.jinja",
        info=group.feed,
        posts=group.posts,
        cursor=group.cursor,
        has_next=group.has_next,
        title=group.feed.name,
    )
