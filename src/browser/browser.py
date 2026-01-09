"""Browser entry and orchestration."""

import gi
import logging

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from ..network.url import URL
from .chrome import Chrome
from .tab import Tab


class Browser:
    def __init__(self):
        self.logger = logging.getLogger("bowser.browser")
        self.app = Gtk.Application(application_id="ch.bowser.bowser")
        self.app.connect("activate", self.on_activate)

        self.tabs = []
        self.active_tab: Tab | None = None
        self.chrome = Chrome(self)

    def _log(self, msg: str, level: int = logging.INFO):
        self.logger.log(level, msg)

    def on_activate(self, app):
        """Called when the application is activated."""
        self._log("Application activated", logging.DEBUG)
        self.chrome.create_window()
        # Build initial tab bar if tabs exist
        self.chrome.rebuild_tab_bar()

    def new_tab(self, url: str):
        tab = Tab(self)
        # Normalize URL to ensure https:// protocol
        url = self._normalize_url(url)
        tab.load(URL(url))
        self.tabs.append(tab)
        self.active_tab = tab
        # Reflect in UI if available
        if self.chrome.tabs_box:
            self.chrome.rebuild_tab_bar()
        self.chrome.update_address_bar()
        self._log(f"New tab opened: {url}", logging.INFO)
        return tab

    def set_active_tab(self, tab: Tab, *_args):
        if tab in self.tabs:
            self.active_tab = tab
            self._log(f"Active tab set: {tab.title}", logging.DEBUG)
            # Update UI highlighting
            if self.chrome.tabs_box:
                self.chrome.rebuild_tab_bar()
            # Trigger repaint of content area
            self.chrome.paint()
            self.chrome.update_address_bar()

    def close_tab(self, tab: Tab, *_args):
        if tab not in self.tabs:
            return
        idx = self.tabs.index(tab)
        self.tabs.remove(tab)
        # Choose new active tab if needed
        if self.active_tab is tab:
            if self.tabs:
                self.active_tab = self.tabs[max(0, idx - 1)]
            else:
                self.active_tab = None
        # Update UI
        if self.chrome.tabs_box:
            self.chrome.rebuild_tab_bar()
        self.chrome.paint()
        self.chrome.update_address_bar()
        self._log(f"Tab closed: {tab.title}", logging.INFO)

    # Navigation and history wrappers
    def navigate_to(self, url_str: str):
        if not url_str:
            return
        # Add https:// if no protocol provided
        url_str = self._normalize_url(url_str)
        if not self.active_tab:
            self.new_tab(url_str)
            return
        self.active_tab.load(URL(url_str))
        self.chrome.paint()
        self.chrome.update_address_bar()
        self._log(f"Navigate to: {url_str}", logging.INFO)

    def _normalize_url(self, url_str: str) -> str:
        """Add https:// protocol if not present."""
        url_str = url_str.strip()
        # If URL already has a protocol, return as-is
        if "://" in url_str:
            return url_str
        # Special about: URLs
        if url_str.startswith("about:"):
            return url_str
        # Otherwise, assume https://
        return f"https://{url_str}"

    def go_back(self):
        if self.active_tab and self.active_tab.go_back():
            self.chrome.paint()
            self.chrome.update_address_bar()
            self._log("Go back", logging.DEBUG)

    def go_forward(self):
        if self.active_tab and self.active_tab.go_forward():
            self.chrome.paint()
            self.chrome.update_address_bar()
            self._log("Go forward", logging.DEBUG)

    def reload(self):
        if self.active_tab:
            self.active_tab.reload()
            self.chrome.paint()
            self.chrome.update_address_bar()
            self._log("Reload", logging.DEBUG)

    def run(self):
        """Start the GTK application main loop."""
        return self.app.run()
