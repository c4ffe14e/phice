import base64
from urllib.parse import urlparse


def base64s(s: str) -> str:
    return base64.standard_b64encode(s.encode()).decode()


def base64s_decode(s: str) -> str:
    return base64.standard_b64decode(s.encode()).decode()


def urlbasename(url: str) -> str:
    return list(filter(None, urlparse(url).path.split("/")))[-1]

def nohostname(url: str) -> str:
    return urlparse(url)._replace(netloc="", scheme="").geturl()
