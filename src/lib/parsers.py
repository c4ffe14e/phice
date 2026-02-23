from contextlib import suppress

from .datatypes import (
    JSON,
    URL,
    AnimatedImage,
    Attachment,
    AttachmentAlbum,
    Comment,
    Event,
    Group,
    Photo,
    Poll,
    Post,
    PostType,
    Reactions,
    Unavailable,
    Unsupported,
    User,
    Video,
)
from .exceptions import ParsingError
from .utils import base64s_decode, urlbasename

REACTIONS_IDS: dict[str, str] = {
    "1635855486666999": "like",
    "1678524932434102": "love",
    "613557422527858": "care",
    "115940658764963": "haha",
    "478547315650144": "wow",
    "908563459236466": "sad",
    "444813342392137": "angry",
}


def parse_reactions(edges: list[JSON]) -> Reactions:
    reactions: Reactions = Reactions()
    for i in edges:
        with suppress(KeyError):
            setattr(reactions, REACTIONS_IDS[i["node"]["id"]], i["reaction_count"])
        reactions.total += i["reaction_count"]

    return reactions


def parse_attachments(style: JSON) -> Attachment:
    attachment: JSON = style["attachment"]
    attachment_type: str = style["__typename"][15:-13]
    media: JSON | None = attachment.get("media", {})
    if media is None:
        return None

    video_fields: JSON = media.get("videoDeliveryLegacyFields", {})
    match attachment_type:
        case "Photo" | "CoverPhoto" | "ProfileMedia" | "3DPhoto":
            photo_url: str
            for k in ("viewer_image", "photo_image", "image", "placeholder_image"):
                if "uri" in media.get(k, {}):
                    photo_url = media[k]["uri"]
                    break
            else:
                raise ParsingError("Can't find the url for the photo")
            owner_id: str | None = None
            if creation_story := media.get("creation_story"):
                owner_id = base64s_decode(creation_story["id"])[4:].split(":", 1)[0]

            return Photo(
                id=media["id"],
                url=photo_url,
                owner_id=owner_id,
                alt_text=media.get("accessibility_caption", ""),
            )
        case "UnifiedLightweightVideo" | "Video":
            return Video(
                id=media["id"],
                url=video_fields["browser_native_hd_url"] or video_fields["browser_native_sd_url"],
                owner_id=media["owner"]["id"],
                thumbnail_url=media["preferred_thumbnail"]["image"]["uri"],
            )
        case "AnimatedImageShare":
            if not video_fields:
                return Photo(url=media["animated_image"]["uri"])
            return AnimatedImage(url=video_fields["browser_native_hd_url"] or video_fields["browser_native_sd_url"])
        case "Album" | "AlbumFrame" | "AlbumColumn":
            subattachments: JSON = attachment.get("all_subattachments", attachment.get("five_photos_subattachments", {}))
            subattachments_items: list[Photo | Video] = []

            for i in subattachments["nodes"]:
                match i["media"]["__typename"]:
                    case "Photo":
                        subattachments_items.append(
                            Photo(
                                id=i["media"]["id"],
                                url=i["media"]["viewer_image"]["uri"],
                                owner_id=i["media"]["owner"]["id"],
                            )
                        )
                    case "Video":
                        sub_video_fields: JSON = i["media"]["video_grid_renderer"]["video"]["videoDeliveryLegacyFields"]
                        subattachments_items.append(
                            Video(
                                id=i["media"]["id"],
                                url=sub_video_fields["browser_native_hd_url"] or sub_video_fields["browser_native_sd_url"],
                                owner_id=i["media"]["owner"]["id"],
                                thumbnail_url=i["media"]["video_grid_renderer"]["video"]["preferred_thumbnail"]["image"]["uri"],
                            )
                        )
                    case _:
                        pass

            return AttachmentAlbum(
                id=attachment["mediaset_token"],
                count=subattachments["count"],
                items=subattachments_items,
                items_left=max(0, subattachments["count"] - len(subattachments_items)),
            )
        case "Share" | "ShareMedium" | "ShareSevere":
            if web_link := attachment["story_attachment_link_renderer"]["attachment"].get("web_link"):
                return URL(url=web_link["url"])
        case "Event":
            return Event(
                title=attachment["target"]["name"],
                time=attachment["target"]["capitalized_day_time_sentence"],
                description=attachment["description"]["text"],
            )
        case "TextPoll":
            poll_nodes: list[JSON] = attachment["target"]["orderedOptions"]["nodes"]
            voters_count: int = sum(i["profile_voters"]["count"] for i in poll_nodes)
            options: list[tuple[str, int, int]] = []
            for i in poll_nodes:
                persent: int = ((i["profile_voters"]["count"] * 100) // voters_count) if voters_count else 0
                options.append((i["text"], i["profile_voters"]["count"], persent))

            return Poll(
                text=attachment["target"]["poll_question_text"],
                total=voters_count,
                options=options,
            )
        case "Unavailable":
            return Unavailable()
        case "Sticker" | "StickerAvatar":
            return Photo(
                url=media["image"]["uri"],
                alt_text=media["label"],
            )
        case "Fallback":
            match media["__typename"]:
                case "Video":
                    return Video(id=media["id"], url=None, thumbnail_url=media["fallback_image"]["uri"])
                case "GenericAttachmentMedia" | "ProfilePicAttachmentMedia":
                    pass
                case _:
                    return Unsupported()
        case "LifeEvent":
            prop: list[JSON] = attachment["properties"]
            return Event(
                title=prop[0]["value"]["text"],
                time=prop[1]["value"]["text"],
            )
        case _:
            return Unsupported()

    return None


def parse_comment(node: JSON) -> Comment:
    author: JSON = node["author"]
    feedback: JSON = node["feedback"]

    username: str | None = None
    if author["url"]:
        username = urlbasename(author["url"])

    comment: Comment = Comment(
        id=node["legacy_fbid"],
        feedback_id=feedback["id"],
        author=User(
            id=author["id"],
            username=username,
            name=author["name"],
            picture_url=author["profile_picture_depth_0"]["uri"],
            verified=author.get("is_verified", False),
        ),
        expansion_token=feedback["expansion_info"]["expansion_token"],
        depth=node["depth"],
        time=node["created_time"],
        replies_count=feedback["replies_fields"]["total_count"],
        reactions=parse_reactions(feedback["top_reactions"]["edges"]),
    )

    if body := node["body"]:
        comment.text = body["text"]

    if attachments := node["attachments"]:
        comment.attachment = parse_attachments(attachments[0]["style_type_renderer"])

    return comment


def parse_post(node: JSON, *, shared: bool = False) -> Post:
    main_node: JSON = node
    story: JSON = node["comet_sections"]["content"]["story"]
    if shared:
        main_node = main_node["attached_story"]
        story = story["attached_story"]
    context_layout: JSON = main_node["comet_sections"]["context_layout"]["story"]["comet_sections"]
    author: JSON = story["actors"][0]
    title: JSON = context_layout["title"]["story"]

    username: str | None = None
    if author["__typename"] != "InstagramUserV2" and author["url"]:
        if author["url"].startswith("https://www.facebook.com/people/"):
            username = base64s_decode(story["id"])[4:].split(":", 1)[0]
        else:
            username = urlbasename(author["url"])

    post: Post = Post(
        id=story["id"],
        post_id=story["post_id"],
        author=User(
            id=author["id"],
            username=username,
            name=author["name"],
            picture_url=author["profile_picture"]["uri"],
        ),
    )

    if title.get("to") and title["to"].get("__typename") == "Group":
        post.from_group = Group(
            id=title["to"]["id"],
            username=urlbasename(title["to"]["url"]),
            name=title["to"]["name"],
        )

    if badge := title.get("comet_sections", {}).get("badge"):
        post.author.verified = badge["__typename"] == "CometFeedUserVerifiedBadgeStrategy"

    if title_text := title.get("title"):
        post.title = title_text["text"]

    if not shared:
        feedback: JSON = node["comet_sections"]["feedback"]["story"]["story_ufi_container"]["story"]["feedback_context"][
            "feedback_target_with_context"
        ]["comet_ufi_summary_and_actions_renderer"]["feedback"]

        post.feedback_id = feedback["id"]
        post.reactions = parse_reactions(feedback["top_reactions"]["edges"])
        post.comments_count = feedback["comment_rendering_instance"]["comments"]["total_count"]
        post.share_count = feedback["share_count"]["count"]
        post.view_count = feedback["video_view_count"]

    for i in context_layout["metadata"]:
        match i["__typename"][5:-8]:
            case "FeedStoryLongerTimestamp" | "FeedStoryMinimizedTimestamp":
                post.time = i["story"]["creation_time"]
            case "StoryUserSignals":
                post.badges.extend(j["title"]["text"] for j in i["story"]["user_signals_info"]["displayed_user_signals"])
            case _:
                pass

    text: list[str] = []
    if message := story["comet_sections"]["message"]:
        if rich_message := message.get("rich_message"):
            text.extend(i["text"] for i in rich_message)
        elif post_text := message["story"].get("message"):
            text.append(post_text["text"])
    if suffix := story["comet_sections"]["message_suffix"]:
        text.append(f" --- {suffix['story']['suffix']['text']}")
    post.text = "\n".join(text)

    if not shared and node["attached_story"]:
        post.attachment = parse_post(node, shared=True)
    elif attachments := story["attachments"]:
        post.attachment = parse_attachments(attachments[0]["styles"])

    if isinstance(post.attachment, Video):
        if "/videos/" in story["wwwURL"]:
            post.post_type = PostType.VIDEO
        elif "/reel/" in story["wwwURL"]:
            post.post_type = PostType.REEL
        post.post_id = post.attachment.id
    elif isinstance(post.attachment, URL):
        if post.attachment.url not in post.text and post.attachment.url[:-1] not in post.text:
            post.text += f"\n{post.attachment.url}"
    elif story["wwwURL"].startswith("https://www.facebook.com/photo"):
        post.post_type = PostType.PHOTO

    return post


def parse_search(edge: JSON) -> User | Post | None:
    role: str = edge["node"]["role"]

    if role in ("ENTITY_PAGES", "ENTITY_USER"):
        profile: JSON = edge["rendering_strategy"]["view_model"]["profile"]

        user: User = User(
            id=profile["id"],
            username=urlbasename(profile["url"]) if profile["url"] else profile["id"],
            name=profile["name"],
            picture_url=profile["profile_picture"]["uri"],
            verified=profile["is_verified"],
        )

        if description := edge["rendering_strategy"]["view_model"]["description_snippets_text_with_entities"]:
            user.description = description[0]["text"]

        return user

    if role == "TOP_PUBLIC_POSTS":
        view: JSON = edge["rendering_strategy"]["view_model"]

        return parse_post(click["story"] if (click := view.get("click_model")) else view["story"])

    return None


def parse_album_item(node: JSON) -> Photo | Video:
    match node["__typename"]:
        case "Photo":
            return Photo(
                id=node["id"],
                url=node["image"]["uri"],
                owner_id=node["owner"]["id"],
            )
        case "Video":
            return Video(
                id=node["id"],
                url=None,
                thumbnail_url=node["image"]["uri"],
                owner_id=node["owner"]["id"],
            )
        case _:
            raise ParsingError(f"Unknown album item type {node['__typename']}")
