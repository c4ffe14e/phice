import orjson

from .api import JSON
from .datatypes import (
    AnimatedImage,
    Comment,
    Event,
    Group,
    Photo,
    Poll,
    Post,
    Unavailable,
    Unsupported,
    User,
    Video,
)
from .exceptions import ParsingError
from .utils import base64s_decode, urlbasename


def parse_reactions(edges: list[JSON]) -> dict[str, int]:
    reactions: dict[str, int] = {
        "like": 0,
        "love": 0,
        "care": 0,
        "haha": 0,
        "wow": 0,
        "sad": 0,
        "angry": 0,
    }
    total: int = 0
    for i in edges:
        total += i["reaction_count"]
        match i["node"]["id"]:
            case "1635855486666999":
                reactions["like"] = i["reaction_count"]
            case "1678524932434102":
                reactions["love"] = i["reaction_count"]
            case "613557422527858":
                reactions["care"] = i["reaction_count"]
            case "115940658764963":
                reactions["haha"] = i["reaction_count"]
            case "478547315650144":
                reactions["wow"] = i["reaction_count"]
            case "908563459236466":
                reactions["sad"] = i["reaction_count"]
            case "444813342392137":
                reactions["angry"] = i["reaction_count"]
            case _:
                pass
    reactions["total"] = total

    return reactions


def parse_comment(node: JSON) -> Comment:
    author: JSON = node["author"]
    feedback: JSON = node["feedback"]

    username: str | None = None
    if author["url"]:
        if author["url"].startswith("https://www.facebook.com/people/") and (
            badges := node.get("discoverable_identity_badges_web")
        ):
            username = orjson.loads(badges[0]["serialized"])["actor_id"]
        else:
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
        is_reply=node["depth"] > 0,
        time=node["created_time"],
        replies_count=feedback["replies_fields"]["total_count"],
        reactions=parse_reactions(feedback["top_reactions"]["edges"]),
    )

    if body := node["body"]:
        comment.text = body["text"]

    if i := node["attachments"]:
        attachments: JSON = i[0]["style_type_renderer"]
        media: JSON = attachments["attachment"]["media"]

        match attachments["__typename"][15:-13]:
            case "Photo":
                comment.attachment = Photo(
                    id=media["id"],
                    url=media["image"]["uri"],
                    alt_text=media["accessibility_caption"],
                )
            case "Video":
                video_url: str = (
                    media["videoDeliveryLegacyFields"]["browser_native_hd_url"]
                    or media["videoDeliveryLegacyFields"]["browser_native_sd_url"]
                )
                comment.attachment = Video(
                    id=media["id"],
                    url=video_url,
                )
            case "AnimatedImageShare":
                if vid := media.get("videoDeliveryLegacyFields"):
                    comment.attachment = AnimatedImage(url=vid["browser_native_hd_url"] or vid["browser_native_sd_url"])
                else:
                    comment.attachment = Photo(
                        url=media["sticker_image"]["uri"],
                        id=media["id"],
                    )
            case "Sticker" | "StickerAvatar":
                comment.attachment = Photo(
                    url=media["image"]["uri"],
                    alt_text=media["label"],
                )
            case "Fallback":
                pass
            case _:
                comment.attachment = Unsupported()

    return comment


def parse_post(node: JSON, *, shared: bool = False) -> Post:
    header: JSON
    content: JSON
    story: JSON
    if shared:
        header = node["attached_story"]["comet_sections"]["context_layout"]["story"]["comet_sections"]
        content = node["comet_sections"]["content"]["story"]["comet_sections"]["attached_story"]["story"]["attached_story"][
            "comet_sections"
        ]["attached_story_layout"]["story"]
        story = node["comet_sections"]["content"]["story"]["attached_story"]
    else:
        header = node["comet_sections"]["context_layout"]["story"]["comet_sections"]
        content = node["comet_sections"]["content"]["story"]
        story = node
    author: JSON = story["actors"][0]
    title: JSON = header["title"]["story"]

    username: str | None = None
    if author["url"]:
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
            picture_url=header["actor_photo"]["story"]["actors"][0]["profile_picture"]["uri"],
        ),
    )

    if (to := node["to"]) and to["__typename"] == "Group":
        post.from_group = Group(
            id=to["id"],
            username=urlbasename(to["url"]),
            name=to["name"],
        )

    if badge := title.get("comet_sections", {}).get("badge"):
        post.author.verified = badge["__typename"] == "CometFeedUserVerifiedBadgeStrategy"

    if t := title.get("title"):
        post.title = t["text"]

    if feedback_container := node["comet_sections"]["feedback"]["story"]["story_ufi_container"]:
        feedback: JSON = feedback_container["story"]["feedback_context"]["feedback_target_with_context"][
            "comet_ufi_summary_and_actions_renderer"
        ]["feedback"]

        post.reactions = parse_reactions(feedback["top_reactions"]["edges"])
        post.comments_count = feedback["comment_rendering_instance"]["comments"]["total_count"]
        post.share_count = feedback["share_count"]["count"]
        post.feedback_id = feedback["id"]
        post.view_count = feedback["video_view_count"]
    else:
        post.reactions = parse_reactions([])

    if not shared and node["attached_story"]:
        post.shared_post = parse_post(node, shared=True)

    for i in header["metadata"]:
        match i["__typename"][5:-8]:
            case "FeedStoryLongerTimestamp" | "FeedStoryMinimizedTimestamp":
                post.time = i["story"]["creation_time"]
            case "StoryUserSignals":
                post.roles.extend(j["title"]["text"] for j in i["story"]["user_signals_info"]["displayed_user_signals"])
            case _:
                pass

    text: list[str] = []
    if message := content["comet_sections"]["message"]:
        if rich_message := message.get("rich_message"):
            text.extend(i["text"] for i in rich_message)
        else:
            text.append(message["story"]["message"]["text"])
        if suffix := content["comet_sections"]["message_suffix"]:
            text.append(f" --- {suffix['story']['suffix']['text']}")

    if i := content["attachments"]:
        styles: JSON = i[0]["styles"]
        attachment: JSON = styles["attachment"]
        media: JSON = attachment.get("media", {})

        match styles["__typename"][15:-13]:
            case "Photo":
                image_url: str = media["photo_image"]["uri"] if media.get("photo_image") else media["placeholder_image"]["uri"]
                post.attachments.append(
                    Photo(
                        id=media["id"],
                        url=image_url,
                        owner_id=author["id"],
                        alt_text=media["accessibility_caption"],
                    )
                )
            case "Video":
                if not post.from_group:
                    post.post_id = media["id"]
                    post.is_video = True
                video_url: str = (
                    media["videoDeliveryLegacyFields"]["browser_native_hd_url"]
                    or media["videoDeliveryLegacyFields"]["browser_native_sd_url"]
                )
                post.attachments.append(
                    Video(
                        id=media["id"],
                        url=video_url,
                        owner_id=media["owner"]["id"],
                    )
                )
            case "Album" | "AlbumFrame" | "AlbumColumn":
                attachments: JSON = attachment.get("five_photos_subattachments") or attachment["all_subattachments"]
                for i in attachments["nodes"]:
                    match i["media"]["__typename"]:
                        case "Photo":
                            post.attachments.append(
                                Photo(
                                    id=i["media"]["id"],
                                    url=i["media"]["viewer_image"]["uri"],
                                    owner_id=i["media"]["owner"]["id"],
                                )
                            )
                        case "Video":
                            video_urls: JSON = i["media"]["video_grid_renderer"]["video"]["videoDeliveryLegacyFields"]
                            post.attachments.append(
                                Video(
                                    id=i["media"]["id"],
                                    url=video_urls["browser_native_hd_url"] or video_urls["browser_native_sd_url"],
                                    owner_id=i["media"]["owner"]["id"],
                                )
                            )
                        case _:
                            post.attachments.append(Unsupported())
                files_count: int = attachments["count"]
                if files_count != len(post.attachments):
                    post.files_left = files_count - len(post.attachments)
            case "Share" | "ShareMedium":
                text.append(attachment["story_attachment_link_renderer"]["attachment"]["web_link"]["url"])
            case "Event":
                post.attachments.append(
                    Event(
                        name=attachment["target"]["name"],
                        description=attachment["description"]["text"],
                        time=attachment["target"]["capitalized_day_time_sentence"],
                    )
                )
            case "ProfileMedia":
                post.attachments.append(Photo(id=media["id"], url=media["image"]["uri"]))
            case "AnimatedImageShare":
                post.attachments.append(
                    AnimatedImage(
                        url=(
                            media["videoDeliveryLegacyFields"]["browser_native_hd_url"]
                            or media["videoDeliveryLegacyFields"]["browser_native_sd_url"]
                        ),
                    )
                )
                post.view_count = None
            case "ShareSevere":
                pass
            case "Unavailable":
                post.attachments.append(Unavailable())
            case "TextPoll":
                voters_count: int = 0
                options: list[tuple[str, int, int]] = []

                for i in attachment["target"]["orderedOptions"]["nodes"]:
                    voters_count += i["profile_voters"]["count"]
                for i in attachment["target"]["orderedOptions"]["nodes"]:
                    persent: int = ((i["profile_voters"]["count"] * 100) // voters_count) if voters_count else 0
                    options.append((i["text"], i["profile_voters"]["count"], persent))

                post.voters_count = voters_count
                post.attachments.append(
                    Poll(
                        text=attachment["target"]["poll_question_text"],
                        total=voters_count,
                        options=options,
                    )
                )
            case _:
                post.attachments.append(Unsupported())
    post.text = "\n".join(text)

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
            raise ParsingError
