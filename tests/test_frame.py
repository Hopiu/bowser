"""Tests for Frame and content loading."""

import pytest
from unittest.mock import Mock, patch
from src.browser.tab import Frame, Tab
from src.network.url import URL


class TestFrame:
    @patch('src.browser.tab.http.request')
    def test_frame_load_success(self, mock_request):
        mock_request.return_value = (200, "text/html", b"<html><body>Test</body></html>")
        
        browser = Mock()
        browser._log = Mock()
        tab = Tab(browser)
        frame = tab.main_frame
        
        url = URL("http://example.com")
        frame.load(url)
        
        assert frame.document is not None
        assert frame.document.tag == "html"
        assert tab.current_url == url
        
    @patch('src.browser.tab.http.request')
    def test_frame_load_404(self, mock_request):
        mock_request.return_value = (404, "text/html", b"Not Found")
        
        browser = Mock()
        browser._log = Mock()
        tab = Tab(browser)
        frame = tab.main_frame
        
        url = URL("http://example.com/missing")
        frame.load(url)
        
        # Should create error document
        assert frame.document is not None
        # Error message in document
        text = frame.document.children[0].children[0].text if frame.document.children else ""
        assert "404" in text or "Error" in text
        
    @patch('src.browser.tab.http.request')
    def test_frame_load_network_error(self, mock_request):
        mock_request.side_effect = Exception("Network unreachable")
        
        browser = Mock()
        browser._log = Mock()
        tab = Tab(browser)
        frame = tab.main_frame
        
        url = URL("http://unreachable.example.com")
        frame.load(url)
        
        # Should create error document
        assert frame.document is not None
        text = frame.document.children[0].children[0].text if frame.document.children else ""
        assert "Error" in text or "unreachable" in text
        
    @patch('src.browser.tab.http.request')
    def test_frame_load_utf8_decode(self, mock_request):
        mock_request.return_value = (200, "text/html", "<html><body>Héllo Wörld</body></html>".encode('utf-8'))
        
        browser = Mock()
        browser._log = Mock()
        tab = Tab(browser)
        frame = tab.main_frame
        
        url = URL("http://example.com")
        frame.load(url)
        
        assert frame.document is not None
        # Should handle UTF-8 characters
        text = frame.document.children[0].children[0].text
        assert "llo" in text  # Part of Héllo
