"""URL parsing and resolution."""

from urllib.parse import urlparse, urljoin


class URL:
    def __init__(self, url: str):
        self._parsed = urlparse(url)

    def resolve(self, relative: str) -> "URL":
        return URL(urljoin(self._parsed.geturl(), relative))

    def origin(self) -> str:
        scheme = self._parsed.scheme
        host = self._parsed.hostname or ""
        port = f":{self._parsed.port}" if self._parsed.port else ""
        return f"{scheme}://{host}{port}"

    def __str__(self) -> str:  # pragma: no cover - convenience
        return self._parsed.geturl()
