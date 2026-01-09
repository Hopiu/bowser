"""Tests for URL normalization."""

import pytest
from src.browser.browser import Browser


class TestURLNormalization:
    def setup_method(self):
        """Create a browser instance for each test."""
        self.browser = Browser()
    
    def test_normalize_url_with_https(self):
        """Test that URLs with https:// protocol are unchanged."""
        url = "https://example.com"
        normalized = self.browser._normalize_url(url)
        assert normalized == "https://example.com"
    
    def test_normalize_url_with_http(self):
        """Test that URLs with http:// protocol are unchanged."""
        url = "http://example.com"
        normalized = self.browser._normalize_url(url)
        assert normalized == "http://example.com"
    
    def test_normalize_url_without_protocol(self):
        """Test that URLs without protocol get https:// added."""
        url = "example.com"
        normalized = self.browser._normalize_url(url)
        assert normalized == "https://example.com"
    
    def test_normalize_url_with_path(self):
        """Test that URLs with path but no protocol get https:// added."""
        url = "example.com/path/to/page"
        normalized = self.browser._normalize_url(url)
        assert normalized == "https://example.com/path/to/page"
    
    def test_normalize_url_with_about(self):
        """Test that about: URLs are not modified."""
        url = "about:startpage"
        normalized = self.browser._normalize_url(url)
        assert normalized == "about:startpage"
    
    def test_normalize_url_strips_whitespace(self):
        """Test that leading/trailing whitespace is stripped."""
        url = "  example.com  "
        normalized = self.browser._normalize_url(url)
        assert normalized == "https://example.com"
    
    def test_normalize_url_with_query_string(self):
        """Test that URLs with query strings work correctly."""
        url = "example.com/search?q=test"
        normalized = self.browser._normalize_url(url)
        assert normalized == "https://example.com/search?q=test"
    
    def test_normalize_url_with_subdomain(self):
        """Test that subdomains work correctly."""
        url = "www.example.com"
        normalized = self.browser._normalize_url(url)
        assert normalized == "https://www.example.com"
    
    def test_normalize_url_with_port(self):
        """Test that ports are preserved."""
        url = "example.com:8080"
        normalized = self.browser._normalize_url(url)
        assert normalized == "https://example.com:8080"
    
    def test_normalize_url_localhost(self):
        """Test that localhost URLs work correctly."""
        url = "localhost:3000"
        normalized = self.browser._normalize_url(url)
        assert normalized == "https://localhost:3000"
