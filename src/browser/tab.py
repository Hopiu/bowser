"""Tab and frame orchestration stubs."""

from typing import Optional

from ..network.url import URL


class Frame:
    def __init__(self, tab: "Tab", parent_frame=None, frame_element=None):
        self.tab = tab
        self.parent_frame = parent_frame
        self.frame_element = frame_element

    def load(self, url: URL, payload: Optional[bytes] = None):
        # TODO: integrate network + parsing + layout + render pipeline
        self.tab.current_url = url


class Tab:
    def __init__(self, browser: "Browser", tab_height: int = 40):
        self.browser = browser
        self.tab_height = tab_height
        self.current_url: Optional[URL] = None
        self.main_frame = Frame(self)

    def load(self, url: URL, payload: Optional[bytes] = None):
        self.main_frame.load(url, payload)
