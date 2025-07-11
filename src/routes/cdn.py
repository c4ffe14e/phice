from collections.abc import Generator
from contextlib import suppress

import httpx
from flask import Blueprint, make_response, request
from werkzeug import Response

from ..flask_utils import get_proxy
from ..lib.wrappers import http_client

bp: Blueprint = Blueprint("cdn", __name__)


@bp.route("/cdn_external/<path:path>", endpoint="cdn_external")
@bp.route("/cdn/<path:path>", endpoint="cdn")
def cdn(path: str) -> Response:
    cdn_url: str = "https://scontent.xx.fbcdn.net" if request.endpoint == "cdn.cdn" else "https://external.fmji4-1.fna.fbcdn.net"
    cdn_headers: dict[str, str] = {}
    if rrange := request.headers.get("range"):
        cdn_headers["range"] = rrange

    client: httpx.Client = http_client(headers=cdn_headers, proxy=get_proxy())
    cdn_request: httpx.Request = client.build_request("GET", f"{cdn_url}/{path}", params=request.query_string)
    cdn_response: httpx.Response = client.send(cdn_request, stream=True)

    headers: dict[str, str] = {
        k: v
        for k, v in cdn_response.headers.items()
        if k
        not in (
            "x-fb-connection-quality",
            "alt-svc",
            "x-robots-tag",
            "connection",
            "content-length",
            "access-control-allow-origin",
            "timing-allow-origin",
            "x-crypto-project",
            "x-additional-error-detail",
            "x-fb-vts-requestid",
        )
    }

    def stream() -> Generator[bytes]:
        with suppress(httpx.ReadTimeout):
            yield from cdn_response.iter_raw()

    response: Response = make_response(stream(), cdn_response.status_code, headers)

    @response.call_on_close
    def close() -> None:  # pyright: ignore[reportUnusedFunction]
        cdn_response.close()
        client.close()

    return response
