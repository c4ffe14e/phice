from flask import Blueprint, abort, render_template, request

from ..flask_utils import get_proxy
from ..lib.exceptions import ParsingError, ResponseError
from ..lib.extractor import Search

bp: Blueprint = Blueprint("search", __name__)


@bp.route("/search")
def search() -> str:
    query: str | None = request.args.get("q")
    if not query:
        abort(400, "Bad query")

    try:
        results = Search(
            query,
            request.args.get("t"),
            request.args.get("cursor"),
            proxy=get_proxy(),
        )
    except (ParsingError, ResponseError) as e:
        abort(500, ", ".join(e.args))

    return render_template(
        "search.html.jinja",
        results=results.results,
        cursor=results.cursor,
        has_next=results.has_next,
        title=query + " - Search",
    )
