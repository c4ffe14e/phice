import tomllib
from importlib import import_module
from pathlib import Path

from flask import Flask

from .config import CustomConfig
from .jinja_filters import FILTERS
from .jinja_globals import GLOBALS
from .lib.utils import deep_merge, dict_check_type


def create_app(config_file: Path) -> Flask:
    app: Flask = Flask(__name__)

    app.config.update(  # pyright: ignore[reportUnknownMemberType]
        {
            "ENABLE_RSS": True,
            "PROXY": None,
            "DEFAULT_SETTINGS": {
                "theme": "default",
                "comments_sort": "filtered",
                "proxy": True,
                "expand": False,
                "timezone": 0,
            },
        }
    )
    if config_file.exists():
        with config_file.open("r", encoding="utf-8") as f:
            deep_merge(app.config, tomllib.loads(f.read()))
    dict_check_type(CustomConfig, app.config)

    app.url_map.strict_slashes = False
    app.jinja_options["autoescape"] = True
    app.jinja_env.filters.update(FILTERS)
    app.jinja_env.globals.update(GLOBALS)

    for route in ("albums", "cdn", "error", "groups", "home", "posts", "profile", "search", "settings", "share"):
        app.register_blueprint(import_module(f".routes.{route}", __name__).bp)

    return app
