from flask import Blueprint, render_template
from flask.typing import ResponseReturnValue

bp: Blueprint = Blueprint("home", __name__)


@bp.route("/")
def home() -> ResponseReturnValue:
    return render_template("home.html.jinja")
