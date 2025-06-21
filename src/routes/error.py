import re
from pathlib import Path
from traceback import format_exception

from flask import Blueprint, render_template
from werkzeug.exceptions import HTTPException, InternalServerError

bp: Blueprint = Blueprint("error_handlers", __name__)


@bp.app_errorhandler(HTTPException)
def error_handler(e: HTTPException) -> tuple[str, int]:
    tb: None | str = None

    if isinstance(e, InternalServerError) and (og := e.original_exception) is not None:
        tb = "".join(format_exception(og))
        tb = re.sub(
            r'File "([^"]*)"',
            lambda m: f'File "{Path(m.group(1) or "").name}"',
            tb,
        )

    return render_template("error.html.jinja", e=e, title="Error", traceback=tb), e.code or 200
