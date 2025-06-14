import httpx
from flask import Blueprint, make_response, request
from werkzeug import Response

bp: Blueprint = Blueprint("cdn", __name__)


@bp.route("/cdn/<path:path>")
def cdn(path: str) -> Response:
    cdn_headers: dict[str, str] = {}
    if rrange := request.headers.get("range"):
        cdn_headers["range"] = rrange

    client: httpx.Client = httpx.Client(headers=cdn_headers)
    cdn_request: httpx.Request = client.build_request("GET", f"https://scontent.xx.fbcdn.net/{path}", params=request.query_string)
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
    response: Response = make_response(cdn_response.iter_raw(), cdn_response.status_code, headers)

    @response.call_on_close
    def close() -> None:  # pyright: ignore[reportUnusedFunction]
        cdn_response.close()
        client.close()

    return response
