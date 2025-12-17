import tomllib
from importlib import import_module
from pathlib import Path
from typing import Any

from flask import Flask

from .jinja_filters import FILTERS
from .jinja_globals import GLOBALS
from .settings import PhiceConfig, UserSettings


def create_app(config_file: Path | None) -> Flask:
    app: Flask = Flask(__name__)

    custom_config: dict[str, Any] = {}
    if config_file and config_file.is_file():
        with config_file.open("r", encoding="utf-8") as f:
            custom_config = tomllib.loads(f.read())

    app.config["phice"] = PhiceConfig(**custom_config.get("phice", {}))
    app.config["user_settings"] = UserSettings(**custom_config.get("default_user_settings", {}))
    app.url_map.strict_slashes = False
    app.jinja_options["autoescape"] = True
    app.jinja_env.filters.update(FILTERS)
    app.jinja_env.globals.update(GLOBALS)

    for route in ("albums", "cdn", "error", "groups", "home", "posts", "profile", "search", "settings", "share"):
        app.register_blueprint(import_module(f".routes.{route}", __name__).bp)

    return app
