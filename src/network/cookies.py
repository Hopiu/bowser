"""In-memory cookie jar (placeholder)."""

from http.cookies import SimpleCookie
from typing import Dict


class CookieJar:
    def __init__(self):
        self._cookies: Dict[str, SimpleCookie] = {}

    def set_cookies(self, origin: str, cookie_header: str) -> None:
        jar = self._cookies.setdefault(origin, SimpleCookie())
        jar.load(cookie_header)

    def get_cookie_header(self, origin: str) -> str:
        jar = self._cookies.get(origin)
        return jar.output(header="", sep="; ").strip() if jar else ""
