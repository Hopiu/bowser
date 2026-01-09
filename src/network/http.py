"""HTTP requests and response handling."""

import http.client
from typing import Optional
import logging

from .url import URL


def request(url: URL, payload: Optional[bytes] = None, method: str = "GET"):
    logger = logging.getLogger("bowser.network")
    parsed = url._parsed
    conn_class = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    conn = conn_class(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    headers = {}
    logger.info(f"HTTP {method} {parsed.scheme}://{parsed.hostname}{path}")
    conn.request(method, path, body=payload, headers=headers)
    resp = conn.getresponse()
    logger.info(f"HTTP response {resp.status} {resp.reason}")
    return resp
