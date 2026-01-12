"""Tab and frame orchestration stubs."""

from typing import Optional, TYPE_CHECKING
import logging

from ..network.url import URL
from ..network import http
from ..parser.html import parse_html, Element
from ..templates import render_startpage, render_error_page

if TYPE_CHECKING:
    from .browser import Browser


class Frame:
    def __init__(self, tab: "Tab", parent_frame=None, frame_element=None):
        self.tab = tab
        self.parent_frame = parent_frame
        self.frame_element = frame_element
        self.document: Optional[Element] = None

    def load(self, url: URL, payload: Optional[bytes] = None):
        """Fetch and parse the URL content."""
        logger = logging.getLogger("bowser.frame")

        # Handle special about: URLs
        url_str = str(url)
        if url_str.startswith("about:startpage"):
            html = render_startpage()
            self.document = parse_html(html)
            self.tab.current_url = url
            return

        if url_str.startswith("about:dom-graph"):
            # Extract path parameter
            from urllib.parse import urlparse, parse_qs
            from ..templates import render_dom_graph_page
            parsed = urlparse(url_str)
            params = parse_qs(parsed.query)
            graph_path = params.get('path', [''])[0]

            html = render_dom_graph_page(graph_path)
            self.document = parse_html(html)
            self.tab.current_url = url
            return

        try:
            status, content_type, body = http.request(url, payload)

            if status == 200:
                # Decode response
                text = body.decode('utf-8', errors='replace')

                # Parse HTML
                self.document = parse_html(text)
                self.tab.current_url = url
            else:
                # Error handling - show error page
                html = render_error_page(status, str(url))
                self.document = parse_html(html)

        except Exception as e:
            # Network error - show error page
            html = render_error_page(0, str(url), str(e))
            self.document = parse_html(html)
            logger.error(f"Failed to load {url}: {e}")


class Tab:
    def __init__(self, browser: "Browser", tab_height: int = 40):
        self.browser = browser
        self.tab_height = tab_height
        self.current_url: Optional[URL] = None
        self.main_frame = Frame(self)
        self.history: list[URL] = []
        self.history_index: int = -1

    def load(self, url: URL, payload: Optional[bytes] = None):
        # push into history (truncate forward)
        if self.history_index < len(self.history) - 1:
            self.history = self.history[: self.history_index + 1]
        self.history.append(url)
        self.history_index += 1
        self.browser._log(f"Tab load: {url}", logging.INFO)
        self.main_frame.load(url, payload)

    def go_back(self) -> bool:
        if self.history_index > 0:
            self.history_index -= 1
            url = self.history[self.history_index]
            self.browser._log("Tab go_back", logging.DEBUG)
            self.main_frame.load(url)
            return True
        return False

    def go_forward(self) -> bool:
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            url = self.history[self.history_index]
            self.browser._log("Tab go_forward", logging.DEBUG)
            self.main_frame.load(url)
            return True
        return False

    def reload(self) -> bool:
        if 0 <= self.history_index < len(self.history):
            url = self.history[self.history_index]
            self.browser._log("Tab reload", logging.DEBUG)
            self.main_frame.load(url)
            return True
        return False

    @property
    def title(self) -> str:
        if self.current_url is None:
            return "New Tab"
        return str(self.current_url)
