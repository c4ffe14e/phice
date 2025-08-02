from flask import Blueprint, abort, render_template, request
from flask.typing import ResponseReturnValue

from ..flask_utils import get_proxy
from ..lib.extractor import get_search

bp: Blueprint = Blueprint("search", __name__)


@bp.route("/search")
def search() -> ResponseReturnValue:
    category: str | None = request.args.get("t")
    query: str | None = request.args.get("q")
    if not query or not category:
        abort(400)

    results, scroll = get_search(query, category, request.args.get("cursor"), proxy=get_proxy())

    return render_template("search.html.jinja", results=results, scroll=scroll, title=f"{query} - Search")
