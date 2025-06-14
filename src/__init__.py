import json
from importlib import import_module

from flask import Flask

from .jinja_filters import FILTERS
from .jinja_globals import GLOBALS


def create_app(config_file: str) -> Flask:
    app: Flask = Flask(__name__)

    app.config.from_file(config_file, load=json.load)
    app.url_map.strict_slashes = False
    app.jinja_options["autoescape"] = True
    app.jinja_env.filters.update(FILTERS)
    app.jinja_env.globals.update(GLOBALS)

    for route in ("albums", "cdn", "error", "groups", "home", "posts", "profile", "search", "settings", "share"):
        app.register_blueprint(import_module(f".routes.{route}", __name__).bp)

    return app
