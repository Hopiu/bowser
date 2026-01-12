"""Tests for template rendering."""

from src.templates import render_template, render_error_page, render_startpage


class TestTemplateRendering:
    def test_render_startpage(self):
        """Test rendering the startpage template."""
        html = render_startpage()

        assert html
        assert "Bowser" in html
        assert "Welcome" in html
        assert "<!DOCTYPE html>" in html

    def test_render_startpage_has_version(self):
        """Test that startpage includes version."""
        html = render_startpage()

        assert "0.0.1" in html

    def test_render_error_404(self):
        """Test rendering 404 error page."""
        html = render_error_page(404, "http://example.com/missing")

        assert html
        assert "404" in html
        assert "example.com/missing" in html
        assert "Not Found" in html

    def test_render_error_500(self):
        """Test rendering 500 error page."""
        html = render_error_page(500, "http://example.com/error")

        assert html
        assert "500" in html
        assert "Server Error" in html

    def test_render_error_network(self):
        """Test rendering network error page."""
        html = render_error_page(0, "http://example.com", "Connection refused")

        assert html
        assert "Network Error" in html
        assert "Connection refused" in html

    def test_render_error_with_custom_context(self):
        """Test error page with custom error message."""
        html = render_error_page(404, "http://example.com", "Custom error message")

        assert "Custom error message" in html

    def test_render_template_with_context(self):
        """Test rendering template with custom context."""
        html = render_template("startpage.html", version="1.0.0")

        assert "1.0.0" in html
