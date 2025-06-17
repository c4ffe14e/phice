import inspect
from pathlib import Path
from typing import Any

import httpx
import orjson

from .exceptions import ResponseError

type JSON = dict[str, Any]

data_path: Path = Path(__file__).resolve().parent / "data"

with (data_path / "doc_ids.json").open("r") as f:
    DOC_IDS: JSON = orjson.loads(f.read())

with (data_path / "extra_variables.json").open("r") as f:
    EXTRA_VARIABLES: JSON = orjson.loads(f.read())


class Api:
    def __init__(self) -> None:
        self.LSD: str = "_"
        self.HEADERS: dict[str, str] = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "zstd",
            "X-FB-LSD": self.LSD,
            "Origin": "https://www.facebook.com",
            "Alt-Used": "www.facebook.com",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "TE": "trailers",
        }
        self.__client: httpx.Client = httpx.Client(
            headers=self.HEADERS,
            base_url="https://www.facebook.com",
            timeout=15,
            transport=httpx.HTTPTransport(retries=5),
        )

    def __fetch(self, doc_id: int, variables: JSON, *, fuck_facebook: bool = False) -> list[JSON]:
        response: httpx.Response = self.__client.post(
            "/api/graphql/",
            data={
                "__a": "1",
                "__comet_req": "15",
                "lsd": self.LSD,
                "variables": orjson.dumps(variables | EXTRA_VARIABLES).decode(),
                "doc_id": doc_id,
            },
        )
        if response.status_code != 200:
            raise ResponseError(f"Facebook returned {response.status_code}")
        result: list[JSON] = [orjson.loads(i) for i in response.text.splitlines()]
        errors: list[JSON] | None = result[0].get("errors")

        if errors and not (fuck_facebook and "field_exception" in errors[0]["message"]):
            raise ResponseError(f"{inspect.stack()[1].function}: " + ", ".join(i["message"] for i in errors))

        return result

    def route(self, url: str, *, redirect: bool = False) -> tuple[JSON | None, str | None]:
        response: httpx.Response = self.__client.post(
            "/ajax/navigation/",
            data={
                "route_url": url,
                "__a": "1",
                "__comet_req": "15",
                "lsd": self.LSD,
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
        self.__client.close()

    def ProfileCometHeaderQuery(self, user_id: str) -> list[JSON]:
        return self.__fetch(
            DOC_IDS["ProfileCometHeaderQuery"],
            {
                "scale": 1,
                "selectedID": user_id,
                "selectedSpaceType": "community",
                "shouldUseFXIMProfilePicEditor": False,
                "userID": user_id,
            },
        )

    def ProfilePlusCometLoggedOutRootQuery(self, user_id: str) -> list[JSON]:
        return self.__fetch(
            DOC_IDS["ProfilePlusCometLoggedOutRootQuery"],
            {
                "scale": 1,
                "userID": user_id,
            },
        )

    def ProfileCometTimelineFeedQuery(self, user_id: str) -> list[JSON]:
        return self.__fetch(
            DOC_IDS["ProfileCometTimelineFeedQuery"],
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
        return self.__fetch(
            DOC_IDS["ProfileCometTimelineFeedRefetchQuery"],
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
        return self.__fetch(
            DOC_IDS["CometSinglePostDialogContentQuery"],
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
        return self.__fetch(
            DOC_IDS["CommentsListComponentsPaginationQuery"],
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
        return self.__fetch(
            DOC_IDS["CommentListComponentsRootQuery"],
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
        return self.__fetch(
            DOC_IDS["Depth1CommentsListPaginationQuery"],
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
        return self.__fetch(
            DOC_IDS["FBReelsRootWithEntrypointQuery"],
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
        return self.__fetch(
            DOC_IDS["CometGroupRootQuery"],
            {
                "groupID": group_id,
                "inviteShortLinkKey": None,
                "isChainingRecommendationUnit": False,
                "scale": 1,
            },
        )

    def GroupsCometDiscussionLayoutRootQuery(self, group_id: str) -> list[JSON]:
        return self.__fetch(
            DOC_IDS["GroupsCometDiscussionLayoutRootQuery"],
            {
                "groupID": group_id,
                "scale": 1,
            },
        )

    def CometGroupDiscussionRootSuccessQuery(self, group_id: str) -> list[JSON]:
        return self.__fetch(
            DOC_IDS["CometGroupDiscussionRootSuccessQuery"],
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
        return self.__fetch(
            DOC_IDS["GroupsCometFeedRegularStoriesPaginationQuery"],
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
        return self.__fetch(
            DOC_IDS["CometPhotoAlbumQuery"],
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
        return self.__fetch(
            DOC_IDS["CometAlbumPhotoCollagePaginationQuery"],
            {
                "count": 14,
                "cursor": cursor,
                "renderLocation": "permalink",
                "scale": 1,
                "id": album_id,
            },
        )

    def CometPhotoRootContentQuery(self, node_id: str) -> list[JSON]:
        return self.__fetch(
            DOC_IDS["CometPhotoRootContentQuery"],
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
        return self.__fetch(
            DOC_IDS["SearchCometResultsPaginatedResultsQuery"],
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
