from collections.abc import Generator
from contextlib import suppress

import httpx
from flask import Blueprint, Response, make_response, request
from flask.typing import ResponseReturnValue

from src.flask_utils import get_config

from ..lib.wrappers import http_client

bp: Blueprint = Blueprint("cdn", __name__)

EXCLUDED_RESPONSE_HEADERS: list[str] = [
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
    "x-fb-ptm-uuid",
]
INCLUDED_REQUEST_HEADERS: list[str] = [
    "range",
]


@bp.route("/cdn_external/<path:path>", endpoint="cdn_external")
@bp.route("/cdn/<path:path>", endpoint="cdn")
def cdn(path: str) -> ResponseReturnValue:
    cdn_host: str = "scontent.xx.fbcdn.net" if request.endpoint == "cdn.cdn" else "external.fmji4-1.fna.fbcdn.net"
    client_headers: dict[str, str] = {k: v for k, v in request.headers.items() if k.lower() in INCLUDED_REQUEST_HEADERS}
    client: httpx.Client = http_client(headers=client_headers, proxy=get_config().proxy)
    try:
        cdn_request: httpx.Request = client.build_request("GET", f"https://{cdn_host}/{path}", params=request.query_string)
        cdn_response: httpx.Response = client.send(cdn_request, stream=True)
    except httpx.RequestError:
        return "", 500

    def stream() -> Generator[bytes]:
        with suppress(httpx.RequestError):
            yield from cdn_response.iter_raw()

    response_headers: dict[str, str] = {k: v for k, v in cdn_response.headers.items() if k.lower() not in EXCLUDED_RESPONSE_HEADERS}
    response: Response = make_response(stream(), cdn_response.status_code, response_headers)

    @response.call_on_close
    def close() -> None:  # pyright: ignore[reportUnusedFunction]
        cdn_response.close()
        client.close()

    return response
