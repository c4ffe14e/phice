from flask import Blueprint, render_template

bp: Blueprint = Blueprint("home", __name__)


@bp.route("/")
def home() -> str:
    return render_template("home.html.jinja")
