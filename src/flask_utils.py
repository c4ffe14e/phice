from typing import cast

from flask import current_app

from .settings import PhiceConfig, UserSettings


def get_config() -> PhiceConfig:
    return cast("PhiceConfig", current_app.config["phice"])


def get_user_settings() -> UserSettings:
    return cast("UserSettings", current_app.config["user_settings"])
