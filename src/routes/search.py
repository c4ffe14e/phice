from flask import Blueprint, abort, render_template, request

from ..lib.extractor import Search

bp: Blueprint = Blueprint("search", __name__)


@bp.route("/search")
def search() -> str:
    query: str | None = request.args.get("q")
    if not query:
        abort(400, "Bad query")

    results = Search(
        query,
        request.args.get("t"),
        request.args.get("cursor"),
    )

    return render_template(
        "search.html.jinja",
        results=results.results,
        cursor=results.cursor,
        has_next=results.has_next,
        title=query + " - Search",
    )
