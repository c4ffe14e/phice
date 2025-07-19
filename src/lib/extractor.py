from collections import defaultdict
from urllib.parse import parse_qs, urlparse

from .api import Api
from .datatypes import JSON, Album, Comment, Feed, Post, User
from .exceptions import NotFound, ParsingError
from .parsers import parse_album_item, parse_comment, parse_post, parse_search
from .utils import base64s, base64s_decode, urlbasename

COMMENT_FILTERS: defaultdict[str, str] = defaultdict(
    lambda: "RANKED_FILTERED_INTENT_V1",
    {
        "all": "RANKED_UNFILTERED_CHRONOLOGICAL_REPLIES_INTENT_V1",
        "newest": "RECENT_ACTIVITY_INTENT_V1",
        "filtered": "RANKED_FILTERED_INTENT_V1",
    },
)
PROFILE_PAGING: int = 3
COMMENT_PAGING: int = 2
GROUP_PAGING: int = 4
ALBUM_PAGING: int = 3
SEARCH_PAGING: int = 3


class GetProfile:
    def __init__(
        self,
        username: str,
        cursor: str | None = None,
        *,
        proxy: str | None = None,
    ) -> None:
        with Api(proxy=proxy) as api:
            route, route_type = api.route(username)
            if not route or route_type != "profile":
                raise NotFound(f"Profile {username} not found")
            user_id: str = route["rootView"]["props"]["userID"]

            header: JSON = api.ProfileCometHeaderQuery(user_id)[0]["data"]["user"]["profile_header_renderer"]["user"]
            side: JSON = api.ProfilePlusCometLoggedOutRootQuery(user_id)[-1]["data"]["profile_tile_sections"]["edges"][0]["node"]
            posts_feed: list[JSON] = api.ProfileCometTimelineFeedQuery(user_id)

            self.cursor: str | None = cursor
            self.has_next: bool = bool(cursor)
            self.posts: list[Post] = []
            self.feed: Feed = Feed(
                id=user_id,
                token=user_id if header["url"].startswith("https://www.facebook.com/people/") else urlbasename(header["url"]),
                name=header["name"],
                verified=header["show_verified_badge_on_profile"],
            )

            if private := header["wem_private_sharing_bundle"]["private_sharing_control_model_for_user"]:
                self.feed.is_private = private["private_sharing_enabled"]

            if profile_pic := header["profilePicLarge"]:
                self.feed.picture_url = profile_pic["uri"]

            if cover := header["cover_photo"]:
                self.feed.cover_url = cover["photo"]["image"]["uri"]

            if header["profile_social_context"]:
                for i in header["profile_social_context"]["content"]:
                    if "followers" in i["text"]["text"]:
                        self.feed.followers = i["text"]["text"].split(" ", 1)[0]
                    elif "following" in i["text"]["text"]:
                        self.feed.following = i["text"]["text"].split(" ", 1)[0]
                    elif "likes" in i["text"]["text"]:
                        self.feed.likes = i["text"]["text"].split(" ", 1)[0]

            if (i := posts_feed[0]["data"]["user"]["delegate_page"]) and (description := i["best_description"]):
                self.feed.description = description["text"]

            if side["profile_tile_section_type"] == "INTRO":
                for i in side["profile_tile_views"]["nodes"][1]["view_style_renderer"]["view"]["profile_tile_items"]["nodes"]:
                    context: JSON = i["node"]["timeline_context_item"]["renderer"]["context_item"]
                    item: dict[str, str | None] = {"text": None, "url": None, "type": None}
                    item["text"] = context["title"]["text"]
                    if context.get("subtitle"):
                        item["text"] += f" {context['subtitle']['text']}"
                    if ranges := context["title"]["ranges"]:
                        url: str | None = ranges[0]["entity"]["url"]
                        if url and url.startswith("https://l.facebook.com/l.php"):
                            item["url"] = parse_qs(urlparse(url).query)["u"][0]
                        else:
                            item["url"] = url
                    item["type"] = i["node"]["timeline_context_item"]["timeline_context_list_item_type"][11:].lower()
                    self.feed.info.append(item)

            if not self.cursor:
                if i := posts_feed[0]["data"]["user"]["timeline_list_feed_units"]["edges"]:
                    self.posts.append(parse_post(i[0]["node"]))
                for i in posts_feed[1:]:
                    if page_info := i["data"].get("page_info"):
                        self.cursor = page_info["end_cursor"]
                        self.has_next = page_info["has_next_page"]
                        break
                else:
                    raise ParsingError("Couldn't find page_info")
            if self.has_next:
                for _ in range(PROFILE_PAGING):
                    response: list[JSON] = api.ProfileCometTimelineFeedRefetchQuery(user_id, self.cursor)
                    rest: list[JSON] = [i for i in response[1:] if "ProfileCometTimelineFeed_user" in i.get("label", "")]

                    if edges := response[0]["data"]["node"]["timeline_list_feed_units"]["edges"]:
                        self.posts.append(parse_post(edges[0]["node"]))
                    self.posts.extend(parse_post(i["data"]["node"]) for i in rest[:-1])
                    self.cursor = rest[-1]["data"]["page_info"]["end_cursor"]
                    self.has_next = rest[-1]["data"]["page_info"]["has_next_page"]
                    if not self.has_next:
                        break


class GetPost:
    def __init__(
        self,
        token: str,
        cursor: str | None = None,
        focus: str | None = None,
        sort: str | None = "filtered",
        *,
        proxy: str | None = None,
    ) -> None:
        with Api(proxy=proxy) as api:
            route, route_type = api.route(token)
            post_id: str | None = None
            if route and route_type:
                match route_type:
                    case "post" | "group_post":
                        post_id = route["rootView"]["props"]["storyID"]
                    case "videos":
                        props: JSON = route["rootView"]["props"]
                        page_id: str = props["pageID"]
                        video_id: str = props["v"]
                        if page_id and video_id:
                            post_id = base64s(f"S:_I{page_id}:{video_id}:{video_id}")
                    case "reel":
                        reel: JSON | None = api.FBReelsRootWithEntrypointQuery(token)[0]["data"]["video"]
                        if reel:
                            reel_owner_id: str = reel["creation_story"]["video"]["owner"]["id"]
                            reel_id: str = reel["creation_story"]["post_id"]
                            post_id = base64s(f"S:_I{reel_owner_id}:{reel_id}:{reel_id}")
                    case "photos":
                        photo: JSON | None = api.CometPhotoRootContentQuery(token)[0]["data"]["currMedia"]
                        if photo:
                            user_id: str = base64s_decode(photo["container_story"]["id"]).split(":")[1]
                            post_id = base64s(f"S:{user_id}:VK:{photo['id']}")
                    case _:
                        pass
            if post_id is None:
                raise NotFound("Post not found")
            sort_type: str | None = None if sort is None else COMMENT_FILTERS[sort]
            post_payload: JSON = api.CometSinglePostDialogContentQuery(post_id, focus)[0]["data"]["node"]

            self.cursor: str | None = cursor
            self.has_next: bool = bool(cursor)
            self.focus: str | None = focus
            self.post: Post = parse_post(post_payload)
            self.comments: list[Comment] = []
            if self.post.feedback_id is not None:
                comments_payload: JSON
                if sort_type:
                    comments_payload = api.CommentListComponentsRootQuery(
                        self.post.feedback_id,
                        sort_type,
                        self.focus,
                    )[0]["data"]["node"]["comment_rendering_instance_for_feed_location"]["comments"]
                else:
                    comments_payload = post_payload["comet_sections"]["feedback"]["story"]["story_ufi_container"]["story"][
                        "feedback_context"
                    ]["feedback_target_with_context"]["comment_list_renderer"]["feedback"][
                        "comment_rendering_instance_for_feed_location"
                    ]["comments"]

                if self.focus:
                    main_comment: JSON = comments_payload["edges"][0]["node"]

                    self.comments.append(parse_comment(main_comment))
                    if not self.cursor:
                        replies: JSON = main_comment["feedback"]["replies_connection"]

                        self.comments.extend(parse_comment(i["node"]) for i in replies["edges"])
                        self.cursor = replies["page_info"]["end_cursor"]
                        self.has_next = replies["page_info"]["has_next_page"]
                    if self.has_next:
                        for _ in range(COMMENT_PAGING):
                            next_replies: JSON = api.Depth1CommentsListPaginationQuery(
                                main_comment["feedback"]["id"],
                                main_comment["feedback"]["expansion_info"]["expansion_token"],
                                self.cursor,
                            )[0]["data"]["node"]["replies_connection"]

                            self.comments.extend(parse_comment(i["node"]) for i in next_replies["edges"])
                            self.cursor = next_replies["page_info"]["end_cursor"]
                            self.has_next = next_replies["page_info"]["has_next_page"]
                            if not self.has_next:
                                break
                else:
                    if not self.cursor:
                        self.comments.extend(parse_comment(i["node"]) for i in comments_payload["edges"])
                        self.cursor = comments_payload["page_info"]["end_cursor"]
                        self.has_next = comments_payload["page_info"]["has_next_page"]
                    if self.has_next:
                        for _ in range(COMMENT_PAGING):
                            next_comments: JSON = api.CommentsListComponentsPaginationQuery(
                                self.post.feedback_id,
                                self.cursor,
                            )[0]["data"]["node"]["comment_rendering_instance_for_feed_location"]["comments"]

                            self.comments.extend(parse_comment(i["node"]) for i in next_comments["edges"])
                            self.cursor = next_comments["page_info"]["end_cursor"]
                            self.has_next = next_comments["page_info"]["has_next_page"]
                            if not self.has_next:
                                break


class GetGroup:
    def __init__(
        self,
        token: str,
        cursor: str | None = None,
        *,
        proxy: str | None = None,
    ) -> None:
        with Api(proxy=proxy) as api:
            route, route_type = api.route(f"groups/{token}")
            if not route or route_type != "group":
                raise NotFound(f"Group {token} not found")
            group_id: str = route["rootView"]["props"]["groupID"]

            header: JSON = api.CometGroupRootQuery(group_id)[0]["data"]["group"]["profile_header_renderer"]["group"]
            side_panel: JSON = api.GroupsCometDiscussionLayoutRootQuery(group_id)[-1]["data"]["comet_discussion_tab_cards"][0][
                "group"
            ]
            posts_feed: list[JSON] = api.CometGroupDiscussionRootSuccessQuery(group_id)

            self.cursor: str | None = cursor
            self.has_next: bool = bool(cursor)
            self.posts: list[Post] = []
            self.feed: Feed = Feed(
                id=group_id,
                token=urlbasename(header["url"]),
                name=header["name"],
                description=side_panel["description_with_entities"]["text"],
                members=header["group_member_profiles"]["formatted_count_text"].split(" ", 1)[0],
                is_group=True,
                is_private=side_panel["privacy_info"]["label"]["text"] == "Private",
            )

            if cover := header["cover_renderer"]["cover_photo_content"]:
                self.feed.cover_url = cover["photo"]["image"]["uri"]

            if locations := side_panel["group_locations"]:
                self.feed.info = [
                    {
                        "type": "location",
                        "text": ", ".join(i["name"] for i in locations),
                        "url": None,
                    }
                ]

            if not self.cursor:
                if post := posts_feed[1]["data"].get("node"):
                    self.posts.append(parse_post(post))
                for i in posts_feed[1:]:
                    if page_info := i["data"].get("page_info"):
                        self.cursor = page_info["end_cursor"]
                        self.has_next = page_info["has_next_page"]
                        break
                else:
                    raise ParsingError("Couldn't find page_info")
            if self.has_next:
                for _ in range(GROUP_PAGING):
                    response: list[JSON] = api.GroupsCometFeedRegularStoriesPaginationQuery(group_id, self.cursor)
                    rest: list[JSON] = [
                        i for i in response[1:] if "GroupsCometFeedRegularStories_group_group_feed" in i.get("label", "")
                    ]

                    if edges := response[0]["data"]["node"]["group_feed"]["edges"]:
                        self.posts.append(parse_post(edges[0]["node"]))
                    self.posts.extend(parse_post(i["data"]["node"]) for i in rest[:-1])
                    self.cursor = rest[-1]["data"]["page_info"]["end_cursor"]
                    self.has_next = rest[-1]["data"]["page_info"]["has_next_page"]
                    if not self.has_next:
                        break


class GetAlbum:
    def __init__(
        self,
        token: str,
        cursor: str | None = None,
        *,
        proxy: str | None = None,
    ) -> None:
        with Api(proxy=proxy) as api:
            album: JSON | None = api.CometPhotoAlbumQuery(token)[0]["data"]["album"]
            if not album:
                raise NotFound("Album not found")

            self.cursor: str | None = cursor
            self.has_next: bool = bool(cursor)
            self.album: Album = Album(
                id=album["id"],
                title=album["title"]["text"],
            )
            if description := album.get("message"):
                self.album.description = description["text"]

            if not self.cursor:
                self.album.items.extend(parse_album_item(i["node"]) for i in album["media"]["edges"])
                self.cursor = album["media"]["page_info"]["end_cursor"]
                self.has_next = album["media"]["page_info"]["has_next_page"]
            if self.has_next:
                for _ in range(ALBUM_PAGING):
                    next_items: JSON = api.CometAlbumPhotoCollagePaginationQuery(album["id"], self.cursor)[0]["data"]["node"][
                        "media"
                    ]

                    self.album.items.extend(parse_album_item(i["node"]) for i in next_items["edges"])
                    self.cursor = next_items["page_info"]["end_cursor"]
                    self.has_next = next_items["page_info"]["has_next_page"]
                    if not self.has_next:
                        break


class Search:
    def __init__(
        self,
        query: str,
        category: str | None,
        cursor: str | None = None,
        *,
        proxy: str | None = None,
    ) -> None:
        self.cursor: str | None = cursor
        self.has_next: bool = bool(cursor)
        self.results: list[User | Post] = []

        with Api(proxy=proxy) as api:
            filters: list[str] = []
            search_type: str
            match category:
                case "posts":
                    search_type = "POSTS_TAB"
                case "recent_posts":
                    search_type = "POSTS_TAB"
                    filters.append('{"name":"recent_posts","args":""}')
                case "people":
                    search_type = "PEOPLE_TAB"
                case _:
                    search_type = "PAGES_TAB"

            for _ in range(SEARCH_PAGING):
                results_payload: JSON = api.SearchCometResultsPaginatedResultsQuery(
                    query,
                    search_type,
                    self.cursor,
                    filters,
                )[0]["data"]["serpResponse"]["results"]

                for i in results_payload["edges"]:
                    item: User | Post | None = parse_search(i)
                    if item is not None:
                        self.results.append(item)

                self.cursor = results_payload["page_info"]["end_cursor"]
                self.has_next = results_payload["page_info"]["has_next_page"]
                if not self.has_next:
                    break
