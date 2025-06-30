import re
import sys
from pathlib import Path

import httpx
import orjson

api_names: list[str] = [
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
]

urls: list[str] = [
    "https://www.facebook.com/facebook",
    "https://www.facebook.com/facebook/posts/1193563419482343",
    "https://www.facebook.com/groups/python/",
    "https://www.facebook.com/media/set/?set=a.10152716010956729",
    "https://www.facebook.com/watch/search/?q=python",
]

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Sec-Fetch-Mode": "navigate",
}


doc_ids: dict[str, int] = {}
extra_vars: dict[str, int] = {}
with httpx.Client(headers=headers) as client:
    for i in urls:
        r: httpx.Response = client.get(i)
        scripts_urls: list[str] = re.findall(r'<link rel="preload" href="(.*)" as="script"', r.text)

        for j in scripts_urls:
            script: str = client.get(j).text

            for name in api_names[:]:
                ids = re.search(rf'^__d\("{name}_facebookRelayOperation",.*exports="([0-9]+)"', script, re.MULTILINE)
                if ids:
                    doc_ids[name] = int(ids.group(1))
                    api_names.remove(name)

            ev: list[str] = re.findall(
                r'name:"(__relay_internal__pv__[^"]+provider)"',
                script,
                re.MULTILINE,
            )
            for v in ev:
                extra_vars[v] = 0

if api_names:
    print("Failed to fetch ids for:", *api_names, file=sys.stderr)

DATA_PATH: Path = Path("src") / "lib" / "data"
with (DATA_PATH / "doc_ids.json").open("w") as f:
    f.write(orjson.dumps(doc_ids, option=orjson.OPT_INDENT_2).decode())

with (DATA_PATH / "extra_variables.json").open("w") as f:
    f.write(orjson.dumps(extra_vars, option=orjson.OPT_INDENT_2).decode())
