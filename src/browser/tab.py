"""Tab and frame orchestration stubs."""

from typing import Optional
import logging

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
