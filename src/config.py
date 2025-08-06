from typing import TypedDict


class DefaultSettings(TypedDict, total=False):
    theme: str
    comments_sort: str
    proxy: bool
    expand: bool
    timezone: int


class CustomConfig(TypedDict, total=False):
    ENABLE_RSS: bool
    PROXY: str | None
    DEFAULT_SETTINGS: DefaultSettings
