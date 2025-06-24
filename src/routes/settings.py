from flask import Blueprint, make_response, redirect, render_template, request, url_for
from werkzeug import Response

bp: Blueprint = Blueprint("settings", __name__)

COOKIE_MAX_AGE: int = 34560000  # 400 days
OPTIONS: list[str] = ["theme", "comments_sort", "proxy", "expand", "timezone"]


@bp.route("/settings", methods=["GET", "POST"])
def settings() -> Response | str:
    if request.method == "POST":
        response: Response = make_response(redirect(request.form.get("referrer", url_for("settings.settings"))))
        if request.form.get("reset"):
            for i in OPTIONS:
                response.delete_cookie(i)
        else:
            for i in OPTIONS:
                response.set_cookie(i, request.form.get(i, ""), max_age=COOKIE_MAX_AGE)
        return response

    return render_template("settings.html.jinja")
