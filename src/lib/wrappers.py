import httpx


def http_client(
    *,
    headers: dict[str, str] | None = None,
    proxy: str | None = None,
    follow_redirects: bool = False,
    base_url: str = "",
) -> httpx.Client:
    client_headers: dict[str, str] = {
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
    if headers is not None:
        client_headers.update(headers)

    return httpx.Client(
        headers=client_headers,
        proxy=proxy,
        timeout=15,
        http2=True,
        follow_redirects=follow_redirects,
        base_url=base_url,
    )
