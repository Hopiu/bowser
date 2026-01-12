"""Tests for browser tab management."""

from unittest.mock import Mock, patch
from src.browser.browser import Browser
from src.browser.tab import Tab
from src.network.url import URL


class TestTab:
    def test_tab_creation(self):
        browser = Mock()
        tab = Tab(browser)
        assert tab.browser is browser
        assert tab.current_url is None
        assert tab.history == []
        assert tab.history_index == -1

    def test_tab_title_new(self):
        browser = Mock()
        tab = Tab(browser)
        assert tab.title == "New Tab"

    def test_tab_title_with_url(self):
        browser = Mock()
        browser._log = Mock()
        tab = Tab(browser)
        tab.load(URL("https://example.com"))
        assert "example.com" in tab.title

    def test_tab_load_adds_history(self):
        browser = Mock()
        browser._log = Mock()
        tab = Tab(browser)
        url1 = URL("https://example.com")
        url2 = URL("https://other.com")

        tab.load(url1)
        assert len(tab.history) == 1
        assert tab.history_index == 0

        tab.load(url2)
        assert len(tab.history) == 2
        assert tab.history_index == 1

    def test_tab_go_back(self):
        browser = Mock()
        browser._log = Mock()
        tab = Tab(browser)
        url1 = URL("https://example.com")
        url2 = URL("https://other.com")

        tab.load(url1)
        tab.load(url2)

        result = tab.go_back()
        assert result is True
        assert tab.history_index == 0

    def test_tab_go_back_at_start(self):
        browser = Mock()
        browser._log = Mock()
        tab = Tab(browser)
        tab.load(URL("https://example.com"))

        result = tab.go_back()
        assert result is False
        assert tab.history_index == 0

    def test_tab_go_forward(self):
        browser = Mock()
        browser._log = Mock()
        tab = Tab(browser)

        tab.load(URL("https://example.com"))
        tab.load(URL("https://other.com"))
        tab.go_back()

        result = tab.go_forward()
        assert result is True
        assert tab.history_index == 1

    def test_tab_go_forward_at_end(self):
        browser = Mock()
        browser._log = Mock()
        tab = Tab(browser)
        tab.load(URL("https://example.com"))

        result = tab.go_forward()
        assert result is False

    def test_tab_reload(self):
        browser = Mock()
        browser._log = Mock()
        tab = Tab(browser)
        tab.load(URL("https://example.com"))

        result = tab.reload()
        assert result is True
        assert tab.history_index == 0

    def test_tab_history_truncation(self):
        browser = Mock()
        browser._log = Mock()
        tab = Tab(browser)

        tab.load(URL("https://example.com"))
        tab.load(URL("https://other.com"))
        tab.load(URL("https://third.com"))
        tab.go_back()  # now at other.com
        tab.load(URL("https://new.com"))  # should truncate third.com

        assert len(tab.history) == 3
        assert tab.history_index == 2


@patch('src.browser.browser.Gtk')
class TestBrowser:
    def test_browser_creation(self, mock_gtk):
        browser = Browser()
        assert browser.tabs == []
        assert browser.active_tab is None

    def test_new_tab(self, mock_gtk):
        browser = Browser()
        browser.chrome.rebuild_tab_bar = Mock()
        browser.chrome.update_address_bar = Mock()

        tab = browser.new_tab("https://example.com")

        assert len(browser.tabs) == 1
        assert browser.active_tab is tab
        assert tab in browser.tabs

    def test_set_active_tab(self, mock_gtk):
        browser = Browser()
        browser.chrome.rebuild_tab_bar = Mock()
        browser.chrome.update_address_bar = Mock()
        browser.chrome.paint = Mock()
        browser.chrome.tabs_box = Mock()

        tab1 = browser.new_tab("https://example.com")
        _ = browser.new_tab("https://other.com")

        browser.set_active_tab(tab1)
        assert browser.active_tab is tab1

    def test_close_tab(self, mock_gtk):
        browser = Browser()
        browser.chrome.rebuild_tab_bar = Mock()
        browser.chrome.update_address_bar = Mock()
        browser.chrome.paint = Mock()
        browser.chrome.tabs_box = Mock()

        tab1 = browser.new_tab("https://example.com")
        tab2 = browser.new_tab("https://other.com")

        browser.close_tab(tab1)

        assert len(browser.tabs) == 1
        assert tab1 not in browser.tabs
        assert browser.active_tab is tab2

    def test_close_active_tab_selects_previous(self, mock_gtk):
        browser = Browser()
        browser.chrome.rebuild_tab_bar = Mock()
        browser.chrome.update_address_bar = Mock()
        browser.chrome.paint = Mock()
        browser.chrome.tabs_box = Mock()

        _ = browser.new_tab("https://example.com")
        tab2 = browser.new_tab("https://other.com")
        tab3 = browser.new_tab("https://third.com")

        browser.close_tab(tab3)
        assert browser.active_tab is tab2

    def test_close_last_tab(self, mock_gtk):
        browser = Browser()
        browser.chrome.rebuild_tab_bar = Mock()
        browser.chrome.update_address_bar = Mock()
        browser.chrome.paint = Mock()
        browser.chrome.tabs_box = Mock()

        tab = browser.new_tab("https://example.com")
        browser.close_tab(tab)

        # When the last tab is closed, a new tab is created
        assert len(browser.tabs) == 1
        assert browser.active_tab is not None

    def test_navigate_to(self, mock_gtk):
        browser = Browser()
        browser.chrome.rebuild_tab_bar = Mock()
        browser.chrome.update_address_bar = Mock()
        browser.chrome.paint = Mock()

        tab = browser.new_tab("https://example.com")
        browser.navigate_to("https://other.com")

        assert len(tab.history) == 2

    def test_navigate_to_no_active_tab(self, mock_gtk):
        browser = Browser()
        browser.chrome.rebuild_tab_bar = Mock()
        browser.chrome.update_address_bar = Mock()

        browser.navigate_to("https://example.com")

        assert len(browser.tabs) == 1
        assert browser.active_tab is not None
