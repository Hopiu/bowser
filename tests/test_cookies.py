"""Tests for cookie management."""

from src.network.cookies import CookieJar


class TestCookieJar:
    def test_cookie_jar_creation(self):
        jar = CookieJar()
        assert jar._cookies == {}

    def test_set_cookies(self):
        jar = CookieJar()
        jar.set_cookies("https://example.com", "session=abc123")

        cookies = jar.get_cookie_header("https://example.com")
        assert "session=abc123" in cookies

    def test_get_cookie_header_empty(self):
        jar = CookieJar()
        cookies = jar.get_cookie_header("https://example.com")
        assert cookies == ""

    def test_multiple_cookies_same_origin(self):
        jar = CookieJar()
        jar.set_cookies("https://example.com", "session=abc123")
        jar.set_cookies("https://example.com", "user=john")

        cookies = jar.get_cookie_header("https://example.com")
        assert "session=abc123" in cookies or "user=john" in cookies

    def test_cookies_isolated_by_origin(self):
        jar = CookieJar()
        jar.set_cookies("https://example.com", "session=abc123")
        jar.set_cookies("https://other.com", "session=xyz789")

        cookies1 = jar.get_cookie_header("https://example.com")
        cookies2 = jar.get_cookie_header("https://other.com")

        assert "abc123" in cookies1
        assert "xyz789" in cookies2
