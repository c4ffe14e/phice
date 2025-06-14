from flask import Blueprint, abort, render_template
from werkzeug.exceptions import HTTPException

from ..lib.exceptions import InvalidResponse, ResponseError

bp: Blueprint = Blueprint("error_handlers", __name__)


@bp.app_errorhandler(HTTPException)
def error_handler(e: HTTPException) -> tuple[str, int]:
    return render_template("error.html.jinja", e=e, title="Error"), e.code or 200


@bp.app_errorhandler(InvalidResponse)
def invaled_reponse_handler(_: InvalidResponse) -> str:
    abort(500, "Invaled response from API")


@bp.app_errorhandler(ResponseError)
def response_error_handler(e: ResponseError) -> str:
    abort(500, str(e))
