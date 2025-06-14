from contextlib import suppress
from urllib.parse import parse_qs, urlparse

from .api import JSON, Api
from .exceptions import InvalidResponse, NotFound
from .parsers import Comment, Feed, Photo, Post, User, Video, parse_comment, parse_post
from .utils import base64s, base64s_decode, urlbasename


class GetProfile:
    def __init__(self, username: str, start_cursor: str | None) -> None:
        api: Api = Api()
        route, route_type = api.route(f"/{username}", redirect=True)
        if not route or route_type != "profile":
            raise NotFound
        user_id: str = route["rootView"]["props"]["userID"]
        header: JSON = api.ProfileCometHeaderQuery(user_id)[0]["data"]["user"]["profile_header_renderer"]["user"]
        side: JSON = api.ProfilePlusCometLoggedOutRootQuery(user_id)[-1]["data"]["profile_tile_sections"]["edges"][0]["node"]
        posts_feed: list[JSON] = api.ProfileCometTimelineFeedQuery(user_id)
        token: str = user_id if header["url"].startswith("https://www.facebook.com/people/") else urlbasename(header["url"])

        self.cursor: str | None = start_cursor
        self.has_next: bool = bool(start_cursor)
        self.posts: list[Post] = []
        self.feed: Feed = Feed(
            id=user_id,
            token=token,
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
                raise InvalidResponse
        if self.has_next:
            for _ in range(3):
                response: list[JSON] = api.ProfileCometTimelineFeedRefetchQuery(user_id, self.cursor)
                rest: list[JSON] = [i for i in response[1:] if "ProfileCometTimelineFeed_user" in i.get("label", "")]

                if edges := response[0]["data"]["node"]["timeline_list_feed_units"]["edges"]:
                    self.posts.append(parse_post(edges[0]["node"]))
                self.posts.extend(parse_post(i["data"]["node"]) for i in rest[:-1])
                self.cursor = rest[-1]["data"]["page_info"]["end_cursor"]
                self.has_next = rest[-1]["data"]["page_info"]["has_next_page"]
                if not self.has_next:
                    break

        api.close()


class GetPost:
    def __init__(self, start_cursor: str | None, focus: str | None = None, sort: str | None = None) -> None:
        self.__api: Api = Api()

        self.id: str | None = None
        self.cursor: str | None = start_cursor
        self.has_next: bool = bool(start_cursor)
        self.focus: str | None = focus
        self.sort: str = {
            "all": "RANKED_UNFILTERED_CHRONOLOGICAL_REPLIES_INTENT_V1",
            "newest": "RECENT_ACTIVITY_INTENT_V1",
        }.get(str(sort), "RANKED_FILTERED_INTENT_V1")
        self.post: Post | None = None
        self.comments: list[Comment] = []

    def __fetch(self) -> None:
        if not self.id:
            raise NotFound
        post_payload: JSON = self.__api.CometSinglePostDialogContentQuery(self.id, self.focus)[0]["data"]["node"]

        self.post = parse_post(post_payload)

        if self.post.feedback_id is not None:
            comments_payload: JSON
            if self.sort:
                comments_payload = self.__api.CommentListComponentsRootQuery(
                    self.post.feedback_id,
                    self.sort,
                    self.focus,
                )[0]["data"]["node"]["comment_rendering_instance_for_feed_location"]["comments"]
            else:
                comments_payload = post_payload["comet_sections"]["feedback"]["story"]["story_ufi_container"]["story"][
                    "feedback_context"
                ]["feedback_target_with_context"]["comment_list_renderer"]["feedback"]["comment_rendering_instance_for_feed_location"][
                    "comments"
                ]

            if self.focus:
                main_comment: JSON = comments_payload["edges"][0]["node"]

                self.comments.append(parse_comment(main_comment))
                if not self.cursor:
                    replies: JSON = main_comment["feedback"]["replies_connection"]

                    self.comments.extend(parse_comment(i["node"]) for i in replies["edges"])
                    self.cursor = replies["page_info"]["end_cursor"]
                    self.has_next = replies["page_info"]["has_next_page"]
                if self.has_next:
                    for _ in range(2):
                        next_replies: JSON = self.__api.Depth1CommentsListPaginationQuery(
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
                    for _ in range(2):
                        next_comments: JSON = self.__api.CommentsListComponentsPaginationQuery(
                            self.post.feedback_id,
                            self.cursor,
                        )[0]["data"]["node"]["comment_rendering_instance_for_feed_location"]["comments"]

                        self.comments.extend(parse_comment(i["node"]) for i in next_comments["edges"])
                        self.cursor = next_comments["page_info"]["end_cursor"]
                        self.has_next = next_comments["page_info"]["has_next_page"]
                        if not self.has_next:
                            break

        self.__api.close()

    def from_post(self, username: str | None, token: str | None) -> None:
        if not username or not token:
            raise NotFound
        route, route_type = self.__api.route(f"/{username}/posts/{token}")
        if not route or route_type != "post":
            raise NotFound
        self.id = route["rootView"]["props"]["storyID"]
        if not self.id:
            raise NotFound
        self.__fetch()

    def from_video(self, username: str, token: str) -> None:
        route, route_type = self.__api.route(f"/{username}/videos/{token}")
        if not route or route_type != "videos":
            raise NotFound
        props: JSON = route["rootView"]["props"]
        page_id: str = props["pageID"]
        post_id: str = props["v"]
        if not page_id or not post_id:
            raise NotFound
        self.id = base64s("S:_I" + page_id + ":" + post_id + ":" + post_id)
        self.__fetch()

    def from_reel(self, video_id: str) -> None:
        reel_id: int = 0
        with suppress(ValueError):
            reel_id = int(video_id)
        video: JSON | None = self.__api.FBReelsRootWithEntrypointQuery(str(reel_id))[0]["data"]["video"]
        if not video:
            raise NotFound
        self.id = video["creation_story"]["id"]
        self.__fetch()

    def from_group_post(self, group_token: str, token: str) -> None:
        route, route_type = self.__api.route(f"/groups/{group_token}/posts/{token}")
        if not route or route_type != "group_post":
            raise NotFound
        self.id = route["rootView"]["props"]["storyID"]
        if not self.id:
            raise NotFound
        self.__fetch()

    def from_photo(self, node_id: str | None) -> None:
        if not node_id:
            raise NotFound
        photo: JSON | None = self.__api.CometPhotoRootContentQuery(node_id)[0]["data"]["currMedia"]
        if not photo:
            raise NotFound
        user_id: str = base64s_decode(photo["container_story"]["id"]).split(":")[1]
        self.id = base64s(f"S:{user_id}:VK:{photo['id']}")
        self.__fetch()


class GetGroup:
    def __init__(self, token: str, start_cursor: str | None) -> None:
        api: Api = Api()
        route, route_type = api.route(f"/groups/{token}")
        if not route or route_type != "group":
            raise NotFound
        group_id: str = route["rootView"]["props"]["groupID"]
        header: JSON = api.CometGroupRootQuery(group_id)[0]["data"]["group"]["profile_header_renderer"]["group"]
        side_panel: JSON = api.GroupsCometDiscussionLayoutRootQuery(group_id)[-1]["data"]["comet_discussion_tab_cards"][0]["group"]
        posts_feed: list[JSON] = api.CometGroupDiscussionRootSuccessQuery(group_id)

        self.cursor: str | None = start_cursor
        self.has_next: bool = bool(start_cursor)
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
                raise InvalidResponse
        if self.has_next:
            for _ in range(4):
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

        api.close()


class GetAlbum:
    def __init__(self, token: str | None, start_cursor: str | None) -> None:
        if not token:
            raise NotFound
        api: Api = Api()
        album: JSON | None = api.CometPhotoAlbumQuery(token)[0]["data"]["album"]
        if not album:
            raise NotFound

        self.cursor: str | None = start_cursor
        self.has_next: bool = bool(start_cursor)
        self.items: list[Photo | Video] = []
        self.title: str = album["title"]["text"]

        items: list[JSON] = []

        if not self.cursor:
            items.extend(album["media"]["edges"])
            self.cursor = album["media"]["page_info"]["end_cursor"]
            self.has_next = album["media"]["page_info"]["has_next_page"]
        if self.has_next:
            for _ in range(3):
                next_items: JSON = api.CometAlbumPhotoCollagePaginationQuery(album["id"], self.cursor)[0]["data"]["node"]["media"]

                items.extend(next_items["edges"])
                self.cursor = next_items["page_info"]["end_cursor"]
                self.has_next = next_items["page_info"]["has_next_page"]
                if not self.has_next:
                    break

        for i in items:
            match i["node"]["__typename"]:
                case "Photo":
                    self.items.append(
                        Photo(
                            id=i["node"]["id"],
                            url=i["node"]["image"]["uri"],
                            owner_id=i["node"]["owner"]["id"],
                        )
                    )
                case "Video":
                    self.items.append(
                        Video(
                            id=i["node"]["id"],
                            url=None,
                            thumbnail_url=i["node"]["image"]["uri"],
                            owner_id=i["node"]["owner"]["id"],
                        )
                    )
                case _:
                    pass

        api.close()


class Search:
    def __init__(self, query: str, category: str | None, start_cursor: str | None) -> None:
        self.cursor: str | None = start_cursor
        self.has_next: bool = bool(start_cursor)
        self.results: list[User | Post] = []
        if not query:
            return

        api: Api = Api()
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

        for _ in range(3):
            results_payload: JSON = api.SearchCometResultsPaginatedResultsQuery(
                query,
                search_type,
                self.cursor,
                filters,
            )[0]["data"]["serpResponse"]["results"]

            for i in results_payload["edges"]:
                match i["node"]["role"]:
                    case "ENTITY_PAGES" | "ENTITY_USER":
                        profile: JSON = i["rendering_strategy"]["view_model"]["profile"]

                        user: User = User(
                            id=profile["id"],
                            username=urlbasename(profile["url"]) if profile["url"] else profile["id"],
                            name=profile["name"],
                            picture_url=profile["profile_picture"]["uri"],
                            verified=profile["is_verified"],
                        )

                        if description := i["rendering_strategy"]["view_model"]["description_snippets_text_with_entities"]:
                            user.description = description[0]["text"]

                        self.results.append(user)
                    case "TOP_PUBLIC_POSTS":
                        view: JSON = i["rendering_strategy"]["view_model"]
                        if click := view.get("click_model"):
                            self.results.append(parse_post(click["story"]))
                        else:
                            self.results.append(parse_post(view["story"]))
                    case "END_OF_RESULTS_INDICATOR":
                        pass
                    case _:
                        raise InvalidResponse

            self.cursor = results_payload["page_info"]["end_cursor"]
            self.has_next = results_payload["page_info"]["has_next_page"]
            if not self.has_next:
                break

        api.close()
