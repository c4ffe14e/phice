import uuid
from typing import Any

from flask import url_for

from .flask_utils import get_config, get_user_settings
from .lib.datatypes import Post, PostType


def types(obj: object) -> str:
    return type(obj).__name__


def post_url(p: Post) -> str:
    author: str = p.author.username or p.author.id

    if p.from_group:
        return url_for("posts.groups_posts", author=p.from_group.username, token=p.post_id)
    if p.post_type == PostType.VIDEO:
        return url_for("posts.videos", author=author, token=p.post_id)
    if p.post_type == PostType.REEL:
        return url_for("posts.reel", token=p.post_id)
    return url_for("posts.posts", author=author, token=p.post_id)


def juuid() -> str:
    return uuid.uuid1().hex


THEMES: dict[str, str] = {
    "default": "Default",
    "light": "Light",
    "black": "Black",
    "catppuccin_mocha": "Catppuccin mocha",
    "catppuccin_latte": "Catppuccin latte",
}

GLOBALS: dict[str, Any] = {
    "type": types,
    "get_config": get_config,
    "get_user_settings": get_user_settings,
    "THEMES": THEMES,
    "post_url": post_url,
    "uuid": juuid,
}
