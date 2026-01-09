"""Browser entry and orchestration."""

from ..network.url import URL
from .tab import Tab


class Browser:
    def __init__(self):
        self.tabs = []
        self.active_tab: Tab | None = None

    def new_tab(self, url: str):
        tab = Tab(self)
        tab.load(URL(url))
        self.tabs.append(tab)
        self.active_tab = tab
        return tab

    def run(self):
        # Placeholder: mainloop hooks into GTK
        pass
