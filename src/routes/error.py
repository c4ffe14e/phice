import re
from pathlib import Path
from traceback import format_exception

from flask import Blueprint, render_template
from werkzeug.exceptions import HTTPException, InternalServerError

from ..lib.exceptions import NotFound, ResponseError

bp: Blueprint = Blueprint("error_handlers", __name__)


@bp.app_errorhandler(NotFound)
@bp.app_errorhandler(ResponseError)
@bp.app_errorhandler(HTTPException)
def error_handler(e: HTTPException | NotFound | ResponseError) -> tuple[str, int]:
    status_code: int = 200
    message: str | None = None
    tb: str | None = None

    match e:
        case NotFound():
            status_code = 404
            message = ", ".join(e.args)
        case ResponseError():
            status_code = 500
            message = e.message
        case InternalServerError():
            if (og := e.original_exception) is not None:
                tb = "".join(format_exception(og))
                tb = re.sub(
                    r'File "([^"]*)"',
                    lambda m: f'File "{Path(m.group(1)).name}"',
                    tb,
                )
        case HTTPException():
            if e.code:
                status_code = e.code
            message = e.description

    return render_template(
        "error.html.jinja",
        title="Error",
        status_code=status_code,
        traceback=tb,
        message=message,
    ), status_code
