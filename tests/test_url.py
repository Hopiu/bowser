"""Tests for URL parsing and resolution."""

import pytest
from src.network.url import URL


class TestURL:
    def test_parse_simple_url(self):
        url = URL("https://example.com")
        assert str(url) == "https://example.com"
        
    def test_parse_url_with_path(self):
        url = URL("https://example.com/path/to/page")
        assert str(url) == "https://example.com/path/to/page"
        
    def test_parse_url_with_query(self):
        url = URL("https://example.com/search?q=test")
        assert str(url) == "https://example.com/search?q=test"
        
    def test_origin(self):
        url = URL("https://example.com:8080/path")
        assert url.origin() == "https://example.com:8080"
        
    def test_origin_default_port(self):
        url = URL("https://example.com/path")
        assert url.origin() == "https://example.com"
        
    def test_resolve_relative_path(self):
        base = URL("https://example.com/dir/page.html")
        resolved = base.resolve("other.html")
        assert str(resolved) == "https://example.com/dir/other.html"
        
    def test_resolve_absolute_path(self):
        base = URL("https://example.com/dir/page.html")
        resolved = base.resolve("/root/page.html")
        assert str(resolved) == "https://example.com/root/page.html"
        
    def test_resolve_full_url(self):
        base = URL("https://example.com/page.html")
        resolved = base.resolve("https://other.com/page.html")
        assert str(resolved) == "https://other.com/page.html"
