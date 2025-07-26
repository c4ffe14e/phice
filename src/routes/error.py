from pathlib import Path
from traceback import format_exception

from flask import Blueprint, current_app, render_template
from werkzeug.exceptions import HTTPException, InternalServerError

from ..lib.exceptions import NotFoundError, ResponseError

bp: Blueprint = Blueprint("error_handlers", __name__)


@bp.app_errorhandler(NotFoundError)
@bp.app_errorhandler(ResponseError)
@bp.app_errorhandler(HTTPException)
def error_handler(e: HTTPException | NotFoundError | ResponseError) -> tuple[str, int]:
    status_code: int = 500
    message: str | None = None
    tb: str | None = None

    match e:
        case NotFoundError():
            status_code = 404
            message = ", ".join(e.args)
        case ResponseError():
            status_code = 500
            message = e.message
        case HTTPException():
            if e.code:
                status_code = e.code
            message = e.description
            if isinstance(e, InternalServerError) and (og := e.original_exception) is not None:
                tb = "".join(format_exception(og)).replace(f"{Path(current_app.root_path).parent}/", "")

    return render_template(
        "error.html.jinja",
        title="Error",
        status_code=status_code,
        traceback=tb,
        message=message,
    ), status_code
