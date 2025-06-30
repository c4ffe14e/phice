import inspect
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import httpx
import orjson
from bs4 import BeautifulSoup, Tag

from .exceptions import RateLimitError, ResponseError
from .wrappers import http_client

type JSON = dict[str, Any]

DATA_PATH: Path = Path(__file__).resolve().parent / "data"

with (DATA_PATH / "doc_ids.json").open("r") as f:
    DOC_IDS: JSON = orjson.loads(f.read())

with (DATA_PATH / "extra_variables.json").open("r") as f:
    EXTRA_VARIABLES: JSON = orjson.loads(f.read())


class Api:
    def __init__(self, *, proxy: str | None = None) -> None:
        self.lsd: str = "_"
        self.client: httpx.Client = http_client(
            headers={
                "Accept": "*/*",
                "X-FB-LSD": self.lsd,
                "Origin": "https://www.facebook.com",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
            },
            base_url="https://www.facebook.com",
            proxy=proxy,
        )

    def fetch(self, name: str, variables: JSON, *, fuck_facebook: bool = False) -> list[JSON]:
        response: httpx.Response = self.client.post(
            "/api/graphql/",
            data={
                "__a": "1",
                "__comet_req": "15",
                "lsd": self.lsd,
                "variables": orjson.dumps(variables | EXTRA_VARIABLES).decode(),
                "doc_id": DOC_IDS[name],
            },
        )
        if response.status_code != 200:
            raise ResponseError(f"Facebook returned {response.status_code}")
        result: list[JSON] = [orjson.loads(i) for i in response.text.splitlines()]
        errors: list[JSON] | None = result[0].get("errors")

        if errors:
            if errors[0].get("code") == 1675004:
                raise RateLimitError
            if not (fuck_facebook and "field_exception" in errors[0]["message"]):
                raise ResponseError(f"{inspect.stack()[1].function}: " + ", ".join(i["message"] for i in errors))

        return result

    def route(self, url: str, *, redirect: bool = False) -> tuple[JSON | None, str | None]:
        response: httpx.Response = self.client.post(
            "/ajax/navigation/",
            data={
                "route_url": url,
                "__a": "1",
                "__comet_req": "15",
                "lsd": self.lsd,
            },
        )
        result: JSON = orjson.loads(response.text[9:])["payload"].get("payload", {}).get("result", {})
        if not result:
            return None, None
        if result["type"] == "route_redirect":
            if redirect:
                result = result["redirect_result"]
            else:
                return None, None

        return result["exports"], result["exports"]["entityKeyConfig"]["entity_type"]["value"]

    def close(self) -> None:
        self.client.close()

    # EXPERIMENTAL
    def from_html(self, url: str) -> dict[str, list[JSON]]:
        response: httpx.Response = self.client.get(
            url,
            follow_redirects=True,
        )
        if response.status_code != 200:
            raise ResponseError(f"Facebook returned {response.status_code}")

        soup: BeautifulSoup = BeautifulSoup(response.text, "lxml")

        data_script_tags = soup.find_all(
            lambda t: t.name == "script" and t.get("type") == "application/json" and not t.has_attr("id")
        )

        ret: defaultdict[str, list[JSON]] = defaultdict(list)
        for tag in data_script_tags:
            if isinstance(tag, Tag) and tag.string is not None:
                try:
                    parsed_json: JSON | list[JSON] = orjson.loads(str(tag.string))["require"][0][3][0]
                except IndexError:
                    continue
                if isinstance(parsed_json, dict) and "__bbox" in parsed_json:
                    for obj in parsed_json["__bbox"]["require"]:
                        if obj[0].startswith("RelayPrefetchedStreamCache"):
                            ret[obj[3][0][4:].rsplit("_", 1)[0][:-14]].append(obj[3][1]["__bbox"]["result"])

        lsd_tag = soup.find("script", id="__eqmc", type="application/json")
        if isinstance(lsd_tag, Tag) and lsd_tag.string is not None:
            self.lsd = orjson.loads(str(lsd_tag.string)).get("l", "_")

        return dict(ret)

    def ProfileCometHeaderQuery(self, user_id: str) -> list[JSON]:
        return self.fetch(
            "ProfileCometHeaderQuery",
            {
                "scale": 1,
                "selectedID": user_id,
                "selectedSpaceType": "community",
                "shouldUseFXIMProfilePicEditor": False,
                "userID": user_id,
            },
        )

    def ProfilePlusCometLoggedOutRootQuery(self, user_id: str) -> list[JSON]:
        return self.fetch(
            "ProfilePlusCometLoggedOutRootQuery",
            {
                "scale": 1,
                "userID": user_id,
            },
        )

    def ProfileCometTimelineFeedQuery(self, user_id: str) -> list[JSON]:
        return self.fetch(
            "ProfileCometTimelineFeedQuery",
            {
                "count": 1,
                "feedbackSource": 0,
                "feedLocation": "TIMELINE",
                "omitPinnedPost": False,
                "privacySelectorRenderLocation": "COMET_STREAM",
                "renderLocation": "timeline",
                "scale": 1,
                "stream_count": 1,
                "userID": user_id,
            },
        )

    def ProfileCometTimelineFeedRefetchQuery(self, user_id: str, cursor: str | None) -> list[JSON]:
        return self.fetch(
            "ProfileCometTimelineFeedRefetchQuery",
            {
                "afterTime": None,
                "beforeTime": None,
                "count": 3,
                "cursor": cursor,
                "feedLocation": "TIMELINE",
                "feedbackSource": 0,
                "focusCommentID": None,
                "memorializedSplitTimeFilter": None,
                "omitPinnedPost": False,
                "postedBy": None,
                "privacy": None,
                "privacySelectorRenderLocation": "COMET_STREAM",
                "renderLocation": "timeline",
                "scale": 1,
                "stream_count": 1,
                "taggedInOnly": None,
                "trackingCode": None,
                "useDefaultActor": False,
                "id": user_id,
            },
        )

    def CometSinglePostDialogContentQuery(self, story_id: str, focus_id: str | None = None) -> list[JSON]:
        return self.fetch(
            "CometSinglePostDialogContentQuery",
            {
                "feedbackSource": 2,
                "feedLocation": "PERMALINK",
                "focusCommentID": focus_id,
                "privacySelectorRenderLocation": "COMET_STREAM",
                "renderLocation": "permalink",
                "scale": 1,
                "storyID": story_id,
                "useDefaultActor": False,
            },
        )

    def CommentsListComponentsPaginationQuery(self, feedback_id: str, cursor: str | None) -> list[JSON]:
        return self.fetch(
            "CommentsListComponentsPaginationQuery",
            {
                "commentsAfterCount": -1,
                "commentsAfterCursor": cursor,
                "commentsBeforeCount": None,
                "commentsBeforeCursor": None,
                "commentsIntentToken": None,
                "feedLocation": "PERMALINK",
                "focusCommentID": None,
                "scale": 1,
                "useDefaultActor": False,
                "id": feedback_id,
            },
        )

    def CommentListComponentsRootQuery(self, feedback_id: str, sort: str, focus_id: str | None = None) -> list[JSON]:
        return self.fetch(
            "CommentListComponentsRootQuery",
            {
                "commentsIntentToken": sort,
                "feedLocation": "PERMALINK",
                "feedbackSource": 2,
                "focusCommentID": focus_id,
                "scale": 1,
                "useDefaultActor": False,
                "id": feedback_id,
            },
        )

    def Depth1CommentsListPaginationQuery(self, feedback_id: str, expansion_token: str, cursor: str | None) -> list[JSON]:
        return self.fetch(
            "Depth1CommentsListPaginationQuery",
            {
                "clientKey": None,
                "expansionToken": expansion_token,
                "feedLocation": "PERMALINK",
                "focusCommentID": None,
                "repliesAfterCount": None,
                "repliesAfterCursor": cursor,
                "repliesBeforeCount": None,
                "repliesBeforeCursor": None,
                "scale": 1,
                "useDefaultActor": False,
                "id": feedback_id,
            },
        )

    def FBReelsRootWithEntrypointQuery(self, reel_id: str) -> list[JSON]:
        return self.fetch(
            "FBReelsRootWithEntrypointQuery",
            {
                "count": 0,
                "group_id_list": [],
                "initial_node_id": reel_id,
                "isAggregationProfileViewerOrShouldShowReelsForPage": True,
                "page_id": "",
                "recent_vpvs_v2": [],
                "renderLocation": "fb_shorts_profile_video_deep_dive",
                "root_video_id": reel_id,
                "root_video_tracking_key": "",
                "scale": 1,
                "shouldIncludeInitialNodeFetch": True,
                "shouldShowReelsForPage": False,
                "surface_type": "FEED_VIDEO_DEEP_DIVE",
                "useDefaultActor": False,
            },
        )

    def CometGroupRootQuery(self, group_id: str) -> list[JSON]:
        return self.fetch(
            "CometGroupRootQuery",
            {
                "groupID": group_id,
                "inviteShortLinkKey": None,
                "isChainingRecommendationUnit": False,
                "scale": 1,
            },
        )

    def GroupsCometDiscussionLayoutRootQuery(self, group_id: str) -> list[JSON]:
        return self.fetch(
            "GroupsCometDiscussionLayoutRootQuery",
            {
                "groupID": group_id,
                "scale": 1,
            },
        )

    def CometGroupDiscussionRootSuccessQuery(self, group_id: str) -> list[JSON]:
        return self.fetch(
            "CometGroupDiscussionRootSuccessQuery",
            {
                "autoOpenChat": False,
                "creative_provider_id": None,
                "feedbackSource": 0,
                "feedLocation": "GROUP",
                "feedType": "DISCUSSION",
                "focusCommentID": None,
                "groupID": group_id,
                "hasHoistStories": False,
                "hoistedSectionHeaderType": "notifications",
                "hoistStories": [],
                "hoistStoriesCount": 0,
                "privacySelectorRenderLocation": "COMET_STREAM",
                "regular_stories_count": 1,
                "regular_stories_stream_initial_count": 1,
                "renderLocation": "group",
                "scale": 1,
                "shouldDeferMainFeed": False,
                "sortingSetting": "RECENT_ACTIVITY",
                "threadID": "",
                "useDefaultActor": False,
            },
            fuck_facebook=True,
        )

    def GroupsCometFeedRegularStoriesPaginationQuery(self, group_id: str, cursor: str | None) -> list[JSON]:
        return self.fetch(
            "GroupsCometFeedRegularStoriesPaginationQuery",
            {
                "count": 3,
                "cursor": cursor,
                "feedLocation": "GROUP",
                "feedType": "DISCUSSION",
                "feedbackSource": 0,
                "focusCommentID": None,
                "privacySelectorRenderLocation": "COMET_STREAM",
                "renderLocation": "group",
                "scale": 1,
                "sortingSetting": "RECENT_ACTIVITY",
                "stream_initial_count": 1,
                "useDefaultActor": False,
                "id": group_id,
            },
        )

    def CometPhotoAlbumQuery(self, token: str) -> list[JSON]:
        return self.fetch(
            "CometPhotoAlbumQuery",
            {
                "feedbackSource": 65,
                "feedLocation": "PERMALINK",
                "focusCommentID": None,
                "mediasetToken": token,
                "privacySelectorRenderLocation": "COMET_STREAM",
                "renderLocation": "permalink",
                "scale": 1,
                "useDefaultActor": False,
            },
        )

    def CometAlbumPhotoCollagePaginationQuery(self, album_id: str, cursor: str | None) -> list[JSON]:
        return self.fetch(
            "CometAlbumPhotoCollagePaginationQuery",
            {
                "count": 14,
                "cursor": cursor,
                "renderLocation": "permalink",
                "scale": 1,
                "id": album_id,
            },
        )

    def CometPhotoRootContentQuery(self, node_id: str) -> list[JSON]:
        return self.fetch(
            "CometPhotoRootContentQuery",
            {
                "feedbackSource": 65,
                "feedLocation": "COMET_MEDIA_VIEWER",
                "privacySelectorRenderLocation": "COMET_MEDIA_VIEWER",
                "renderLocation": "comet_media_viewer",
                "scale": 1,
                "useDefaultActor": False,
                "isMediaset": True,
                "mediasetToken": "",
                "nodeID": node_id,
                "focusCommentID": None,
            },
        )

    def SearchCometResultsPaginatedResultsQuery(
        self,
        query: str,
        category: str,
        cursor: str | None,
        filters: list[str] | None = None,
    ) -> list[JSON]:
        return self.fetch(
            "SearchCometResultsPaginatedResultsQuery",
            {
                "allow_streaming": False,
                "args": {
                    "callsite": "COMET_GLOBAL_SEARCH",
                    "config": {
                        "exact_match": False,
                        "high_confidence_config": None,
                        "intercept_config": None,
                        "sts_disambiguation": None,
                        "watch_config": None,
                    },
                    "context": {},
                    "experience": {
                        "client_defined_experiences": ["ADS_PARALLEL_FETCH"],
                        "encoded_server_defined_params": None,
                        "fbid": None,
                        "type": category,
                    },
                    "filters": filters or [],
                    "text": query,
                },
                "count": 5,
                "cursor": cursor,
                "feedLocation": "SEARCH",
                "feedbackSource": 23,
                "fetch_filters": True,
                "focusCommentID": None,
                "locale": None,
                "privacySelectorRenderLocation": "COMET_STREAM",
                "renderLocation": "search_results_page",
                "scale": 1,
                "stream_initial_count": 0,
                "useDefaultActor": False,
            },
        )
