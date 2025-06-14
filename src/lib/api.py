import inspect
from typing import Any

import httpx
import orjson

from .exceptions import ResponseError

type JSON = dict[str, Any]

EXTRA_VARIABLES: JSON = {
    "__relay_internal__pv__ProfileCometHeaderPrimaryActionBar_passesCometProfileDirectoryGKrelayprovider": False,
    "__relay_internal__pv__GHLShouldChangeAdIdFieldNamerelayprovider": False,
    "__relay_internal__pv__GHLShouldChangeSponsoredDataFieldNamerelayprovider": False,
    "__relay_internal__pv__IsWorkUserrelayprovider": False,
    "__relay_internal__pv__FBReels_deprecate_short_form_video_context_gkrelayprovider": False,
    "__relay_internal__pv__CometImmersivePhotoCanUserDisable3DMotionrelayprovider": False,
    "__relay_internal__pv__WorkCometIsEmployeeGKProviderrelayprovider": False,
    "__relay_internal__pv__IsMergQAPollsrelayprovider": False,
    "__relay_internal__pv__FBReelsMediaFooter_comet_enable_reels_ads_gkrelayprovider": False,
    "__relay_internal__pv__CometUFIReactionsEnableShortNamerelayprovider": False,
    "__relay_internal__pv__CometUFIShareActionMigrationrelayprovider": True,
    "__relay_internal__pv__CometUFI_dedicated_comment_routable_dialog_gkrelayprovider": False,
    "__relay_internal__pv__StoriesArmadilloReplyEnabledrelayprovider": False,
    "__relay_internal__pv__FBReelsIFUTileContent_reelsIFUPlayOnHoverrelayprovider": False,
    "__relay_internal__pv__GroupsCometGroupChatLazyLoadLastMessageSnippetrelayprovider": False,
    "__relay_internal__pv__GroupsCometLazyLoadFeaturedSectionrelayprovider": False,
}


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
        )

    def __fetch(self, doc_id: str, variables: JSON, *, fuck_facebook: bool = False) -> list[JSON]:
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
            raise ResponseError(f"Facebook return {response.status_code}")
        result: list[JSON] = [orjson.loads(i) for i in response.text.splitlines()]
        if (errors := result[0].get("errors")) and not (
            fuck_facebook and "A server error field_exception occured." in errors[0]["message"]
        ):
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
            "24637479539185522",
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
            "29764188139896558",
            {
                "scale": 1,
                "userID": user_id,
            },
        )

    def ProfileCometTimelineFeedQuery(self, user_id: str) -> list[JSON]:
        return self.__fetch(
            "24130362143235169",
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
            "29857242777255325",
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
            "30329081383349461",
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
            "24152478804356082",
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
            "9884198138336503",
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
            "24355745037360129",
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
            "30094271533520445",
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
            "24726713260250827",
            {
                "groupID": group_id,
                "inviteShortLinkKey": None,
                "isChainingRecommendationUnit": False,
                "scale": 1,
            },
        )

    def GroupsCometDiscussionLayoutRootQuery(self, group_id: str) -> list[JSON]:
        return self.__fetch(
            "29803864032592554",
            {
                "groupID": group_id,
                "scale": 1,
            },
        )

    def CometGroupDiscussionRootSuccessQuery(self, group_id: str) -> list[JSON]:
        return self.__fetch(
            "23997107266592174",
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
            "9755367644572581",
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
            "29989561257355685",
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
            "9782410388506700",
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
            "23916701474613206",
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
            "23897855153159069",
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
