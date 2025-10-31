import re
import sys
from pathlib import Path

import httpx
import orjson

QUERY_NAMES: list[str] = [
    "CometAlbumPhotoCollagePaginationQuery",
    "CometGroupDiscussionRootSuccessQuery",
    "CometGroupRootQuery",
    "CometPhotoAlbumQuery",
    "CometPhotoRootContentQuery",
    "CometSinglePostDialogContentQuery",
    "CommentListComponentsRootQuery",
    "CommentsListComponentsPaginationQuery",
    "Depth1CommentsListPaginationQuery",
    "FBReelsRootWithEntrypointQuery",
    "GroupsCometDiscussionLayoutRootQuery",
    "GroupsCometFeedRegularStoriesPaginationQuery",
    "ProfileCometHeaderQuery",
    "ProfileCometTimelineFeedQuery",
    "ProfileCometTimelineFeedRefetchQuery",
    "ProfilePlusCometLoggedOutRootQuery",
    "SearchCometResultsPaginatedResultsQuery",
    "CometFeedStoryMenuQuery",
]
URLS: list[str] = [
    "https://www.facebook.com/facebook",
    "https://www.facebook.com/facebook/posts/1193563419482343",
    "https://www.facebook.com/reel/3894716004079577",
    "https://www.facebook.com/groups/python",
    "https://www.facebook.com/media/set/?set=a.10152716010956729",
    "https://www.facebook.com/photo/?fbid=10152716011096729&set=a.10152716010956729",
    "https://www.facebook.com/watch/search/?q=python",
]
HEADERS: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Alt-Used": "www.facebook.com",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "TE": "trailers",
}
DATA_PATH: Path = Path("src") / "lib" / "data"


def main() -> int:
    doc_ids: dict[str, int] = {}
    extra_vars: dict[str, int] = {}

    with httpx.Client(headers=HEADERS) as client:
        for url in URLS:
            html_res: httpx.Response = client.get(url)
            scripts_urls: list[str] = re.findall(r'<link rel="preload" href="(.*)" as="script"', html_res.text)

            for script in scripts_urls:
                script_res: httpx.Response = client.get(script)
                script_cont: str = script_res.text

                for name in QUERY_NAMES.copy():
                    id_match: re.Match[str] | None = re.search(
                        rf'^__d\("{name}_facebookRelayOperation",.*exports="([0-9]+)"',
                        script_cont,
                        re.MULTILINE,
                    )
                    if id_match:
                        doc_ids[name] = int(id_match.group(1))
                        QUERY_NAMES.remove(name)

                extra_variables_matches: list[str] = re.findall(
                    r'__relay_internal__pv__.+?provider',
                    script_cont,
                    re.MULTILINE,
                )
                for var in extra_variables_matches:
                    extra_vars[var] = 0

    if QUERY_NAMES:
        print("Failed to fetch ids for:", *QUERY_NAMES, file=sys.stderr)
        return 1

    with (DATA_PATH / "doc_ids.json").open("w") as f:
        f.write(orjson.dumps(doc_ids, option=orjson.OPT_INDENT_2).decode())

    with (DATA_PATH / "extra_variables.json").open("w") as f:
        f.write(orjson.dumps(extra_vars, option=orjson.OPT_INDENT_2).decode())

    return 0


if __name__ == "__main__":
    sys.exit(main())
