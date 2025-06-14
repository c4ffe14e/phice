from typing import cast

from flask import Blueprint, current_app, make_response, redirect, render_template, request, url_for
from werkzeug import Response

bp: Blueprint = Blueprint("settings", __name__)

COOKIE_MAX_AGE: int = 34560000 # 400 days

@bp.route("/settings", methods=["GET", "POST"])
def settings() -> Response | str:
    default_settings: dict[str, str] = cast("dict[str, str]", current_app.config["DEFAULT_SETTINGS"])

    if request.method == "POST":
        response: Response = make_response(redirect(request.form.get("referrer", url_for("settings.settings"))))
        if request.form.get("reset"):
            for k, v in default_settings.items():
                response.set_cookie(k, v, max_age=COOKIE_MAX_AGE)
        else:
            for i in default_settings:
                response.set_cookie(i, request.form.get(i, "off"), max_age=COOKIE_MAX_AGE)
        return response

    return render_template("settings.html.jinja")
