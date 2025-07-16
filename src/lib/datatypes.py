from dataclasses import dataclass, field
from typing import Any

type JSON = dict[str, Any]


@dataclass
class Unsupported:
    pass


@dataclass
class Unavailable:
    pass


@dataclass(kw_only=True)
class Photo:
    url: str
    id: str | None = None
    owner_id: str | None = None
    alt_text: str = ""


@dataclass(kw_only=True)
class Video:
    id: str
    url: str | None
    owner_id: str | None = None
    thumbnail_url: str | None = None


@dataclass(kw_only=True)
class AnimatedImage:
    url: str


@dataclass(kw_only=True)
class Event:
    name: str
    description: str
    time: str


@dataclass(kw_only=True)
class Poll:
    text: str
    total: int
    options: list[tuple[str, int, int]] = field(default_factory=list)


@dataclass(kw_only=True)
class Feed:
    id: str
    token: str
    name: str
    verified: bool = False
    picture_url: str | None = None
    cover_url: str | None = None
    description: str = ""
    followers: str | None = None
    following: str | None = None
    likes: str | None = None
    members: str | None = None
    is_group: bool = False
    is_private: bool = False
    info: list[dict[str, str | None]] = field(default_factory=list)


@dataclass(kw_only=True)
class User:
    id: str
    username: str | None
    name: str
    picture_url: str
    verified: bool = False
    description: str = ""


@dataclass(kw_only=True)
class Group:
    id: str
    username: str
    name: str


@dataclass(kw_only=True)
class Post:
    id: str
    post_id: str
    author: User
    from_group: Group | None = None
    is_video: bool = False
    feedback_id: str | None = None
    text: str = ""
    title: str | None = None
    time: int = 0
    attachments: list[Unsupported | Photo | Video | Event | Unavailable | Poll | AnimatedImage] = field(default_factory=list)
    files_left: int = 0
    reactions: dict[str, int] = field(default_factory=dict)
    comments_count: int = 0
    share_count: int = 0
    view_count: int | None = None
    roles: list[str] = field(default_factory=list)
    shared_post: "Post | None" = None
    voters_count: int | None = None


@dataclass(kw_only=True)
class Comment:
    id: str
    feedback_id: str
    author: User
    expansion_token: str
    is_reply: bool
    text: str = ""
    time: int = 0
    replies_count: int = 0
    reactions: dict[str, int] = field(default_factory=dict)
    attachment: Photo | Video | Unsupported | AnimatedImage | None = None


@dataclass(kw_only=True)
class Album:
    id: str
    title: str
    description: str = ""
    items: list[Photo | Video] = field(default_factory=list)
