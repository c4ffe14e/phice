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


type PostAttachment = Unsupported | Photo | Video | Event | Unavailable | Poll | AnimatedImage
type CommentAttachment = Photo | Video | Unsupported | AnimatedImage | None
type AlbumItem = Photo | Video


@dataclass(kw_only=True)
class Reactions:
    like: int = 0
    love: int = 0
    care: int = 0
    haha: int = 0
    wow: int = 0
    sad: int = 0
    angry: int = 0
    total: int = 0


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
    reactions: Reactions = field(default_factory=Reactions)
    attachment: CommentAttachment = None


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
    attachments: list[PostAttachment] = field(default_factory=list)
    files_left: int = 0
    reactions: Reactions = field(default_factory=Reactions)
    comments_count: int = 0
    share_count: int = 0
    view_count: int | None = None
    badges: list[str] = field(default_factory=list)
    shared_post: "Post | None" = None
    voters_count: int | None = None
    comments: list[Comment] = field(default_factory=list)


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
    posts: list[Post] = field(default_factory=list)


@dataclass(kw_only=True)
class Album:
    id: str
    title: str
    description: str = ""
    items: list[AlbumItem] = field(default_factory=list)


type SearchItem = User | Post


@dataclass
class Scroll:
    cursor: str | None
    has_next: bool | None = None
    rate_limited: bool = False

    def __post_init__(self) -> None:
        if self.has_next is None:
            self.has_next = bool(self.cursor)
