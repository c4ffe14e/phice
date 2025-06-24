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

def get_user_agent() -> str:
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0"
