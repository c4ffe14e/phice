from flask import Blueprint, abort, render_template, request

from ..flask_utils import get_proxy
from ..lib.extractor import Search

bp: Blueprint = Blueprint("search", __name__)


@bp.route("/search")
def search() -> str:
    category: str | None = request.args.get("t")
    query: str | None = request.args.get("q")
    if not query or not category:
        abort(400)

    results = Search(
        query,
        category,
        request.args.get("cursor"),
        proxy=get_proxy(),
    )

    return render_template(
        "search.html.jinja",
        results=results.results,
        cursor=results.cursor,
        has_next=results.has_next,
        title=query + " - Search",
    )
