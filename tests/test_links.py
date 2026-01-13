"""Tests for link parsing, rendering, and navigation."""

import pytest

from src.parser.html import parse_html, parse_html_with_styles, Element, Text
from src.layout.document import DocumentLayout, LayoutLine
from src.network.url import URL


class TestLinkParsing:
    """Tests for parsing anchor elements from HTML."""

    def test_parse_simple_link(self):
        """Test parsing a simple anchor tag."""
        html = "<html><body><a href='https://example.com'>Click here</a></body></html>"
        root = parse_html(html)

        # Find the anchor element
        body = root.children[0]
        assert body.tag == "body"
        anchor = body.children[0]
        assert anchor.tag == "a"
        assert anchor.attributes.get("href") == "https://example.com"

    def test_parse_link_with_text(self):
        """Test that link text content is preserved."""
        html = "<html><body><a href='/page'>Link Text</a></body></html>"
        root = parse_html(html)

        body = root.children[0]
        anchor = body.children[0]
        assert len(anchor.children) == 1
        assert isinstance(anchor.children[0], Text)
        assert anchor.children[0].text.strip() == "Link Text"

    def test_parse_link_in_paragraph(self):
        """Test parsing a link inside a paragraph."""
        html = "<html><body><p>Visit <a href='https://test.com'>our site</a> today!</p></body></html>"
        root = parse_html(html)

        body = root.children[0]
        # The parser may flatten this - check for anchor presence
        found_anchor = False

        def find_anchor(node):
            nonlocal found_anchor
            if isinstance(node, Element) and node.tag == "a":
                found_anchor = True
                assert node.attributes.get("href") == "https://test.com"
            if hasattr(node, "children"):
                for child in node.children:
                    find_anchor(child)

        find_anchor(body)
        assert found_anchor, "Anchor element not found"

    def test_parse_link_with_relative_href(self):
        """Test parsing a link with a relative URL."""
        html = "<html><body><a href='/about'>About</a></body></html>"
        root = parse_html(html)

        body = root.children[0]
        anchor = body.children[0]
        assert anchor.attributes.get("href") == "/about"

    def test_parse_link_with_anchor_href(self):
        """Test parsing a link with an anchor reference."""
        html = "<html><body><a href='#section'>Jump</a></body></html>"
        root = parse_html(html)

        body = root.children[0]
        anchor = body.children[0]
        assert anchor.attributes.get("href") == "#section"


class TestLinkLayout:
    """Tests for link layout and styling."""

    def test_link_layout_has_href(self):
        """Test that layout lines for links include href."""
        html = "<html><body><a href='https://example.com'>Link</a></body></html>"
        root = parse_html_with_styles(html)

        layout = DocumentLayout(root)
        layout.layout(800)

        # Find line with href
        link_lines = [line for line in layout.lines if line.href]
        assert len(link_lines) > 0, "No link lines found"
        assert link_lines[0].href == "https://example.com"

    def test_link_layout_has_color(self):
        """Test that layout lines for links have a color."""
        html = "<html><body><a href='https://example.com'>Link</a></body></html>"
        root = parse_html_with_styles(html)

        layout = DocumentLayout(root)
        layout.layout(800)

        # Find line with color
        link_lines = [line for line in layout.lines if line.href]
        assert len(link_lines) > 0
        # Should have either CSS-specified color or default link color
        assert link_lines[0].color is not None

    def test_non_link_has_no_href(self):
        """Test that non-link elements don't have href."""
        html = "<html><body><p>Regular paragraph</p></body></html>"
        root = parse_html_with_styles(html)

        layout = DocumentLayout(root)
        layout.layout(800)

        # All lines should have no href
        for line in layout.lines:
            assert line.href is None

    def test_layout_line_constructor(self):
        """Test LayoutLine constructor with color and href."""
        line = LayoutLine(
            text="Click me",
            x=10,
            y=20,
            font_size=14,
            color="#0066cc",
            href="https://example.com"
        )

        assert line.text == "Click me"
        assert line.color == "#0066cc"
        assert line.href == "https://example.com"

    def test_layout_line_default_values(self):
        """Test LayoutLine defaults for color and href."""
        line = LayoutLine(
            text="Normal text",
            x=10,
            y=20,
            font_size=14
        )

        assert line.color is None
        assert line.href is None


class TestLinkURLResolution:
    """Tests for URL resolution of links."""

    def test_resolve_absolute_url(self):
        """Test that absolute URLs are preserved."""
        base = URL("https://example.com/page")
        resolved = base.resolve("https://other.com/path")
        assert str(resolved) == "https://other.com/path"

    def test_resolve_relative_url(self):
        """Test resolving a relative URL."""
        base = URL("https://example.com/page")
        resolved = base.resolve("/about")
        assert str(resolved) == "https://example.com/about"

    def test_resolve_relative_path(self):
        """Test resolving a relative path."""
        base = URL("https://example.com/dir/page")
        resolved = base.resolve("other")
        assert str(resolved) == "https://example.com/dir/other"

    def test_resolve_parent_relative(self):
        """Test resolving a parent-relative path."""
        base = URL("https://example.com/dir/subdir/page")
        resolved = base.resolve("../other")
        assert str(resolved) == "https://example.com/dir/other"

    def test_resolve_anchor_only(self):
        """Test resolving an anchor-only URL."""
        base = URL("https://example.com/page")
        resolved = base.resolve("#section")
        assert str(resolved) == "https://example.com/page#section"

    def test_resolve_query_string(self):
        """Test resolving a URL with query string."""
        base = URL("https://example.com/page")
        resolved = base.resolve("?query=value")
        assert str(resolved) == "https://example.com/page?query=value"


class TestRenderPipelineColorParsing:
    """Tests for color parsing in the render pipeline.

    Note: These tests only run when skia is NOT mocked (i.e., when run in isolation).
    When run after test_render.py, skia becomes a MagicMock and these tests are skipped.
    """

    def test_parse_hex_color_6digit(self):
        """Test parsing 6-digit hex colors."""
        from src.render.pipeline import RenderPipeline
        import skia

        # Skip if skia is mocked
        if hasattr(skia.Color, '_mock_name'):
            pytest.skip("skia is mocked")

        pipeline = RenderPipeline()
        color = pipeline._parse_color("#0066cc")

        # Extract RGB components (Skia color is ARGB)
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF

        assert r == 0x00
        assert g == 0x66
        assert b == 0xcc

    def test_parse_hex_color_3digit(self):
        """Test parsing 3-digit hex colors."""
        from src.render.pipeline import RenderPipeline
        import skia

        # Skip if skia is mocked
        if hasattr(skia.Color, '_mock_name'):
            pytest.skip("skia is mocked")

        pipeline = RenderPipeline()
        color = pipeline._parse_color("#abc")

        # #abc should expand to #aabbcc
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF

        # Each digit is doubled: a->aa, b->bb, c->cc
        # But our implementation uses int("a" * 2, 16) which is int("aa", 16) = 170
        assert r == 0xaa
        assert g == 0xbb
        assert b == 0xcc

    def test_parse_named_color(self):
        """Test parsing named colors."""
        from src.render.pipeline import RenderPipeline
        import skia

        # Skip if skia is mocked
        if hasattr(skia.ColorBLACK, '_mock_name'):
            pytest.skip("skia is mocked")

        pipeline = RenderPipeline()

        # Test that named colors return a valid integer color value
        black = pipeline._parse_color("black")
        white = pipeline._parse_color("white")
        red = pipeline._parse_color("red")

        # Black should be 0xFF000000 (opaque black in ARGB)
        assert isinstance(black, int)
        assert (black & 0xFFFFFF) == 0x000000  # RGB is 0

        # White is converted to black because it would be invisible on white bg
        assert isinstance(white, int)
        assert (white & 0xFFFFFF) == 0x000000  # Converted to black

        # Red should have R=255, G=0, B=0
        assert isinstance(red, int)
        r = (red >> 16) & 0xFF
        assert r == 0xFF  # Red component should be 255

    def test_parse_invalid_color_returns_black(self):
        """Test that invalid colors return black."""
        from src.render.pipeline import RenderPipeline
        import skia

        # Skip if skia is mocked
        if hasattr(skia.ColorBLACK, '_mock_name'):
            pytest.skip("skia is mocked")

        pipeline = RenderPipeline()

        invalid = pipeline._parse_color("invalid")
        invalid2 = pipeline._parse_color("#xyz")
        invalid3 = pipeline._parse_color("")

        # All should return black (integer value)
        assert isinstance(invalid, int)
        assert isinstance(invalid2, int)
        assert isinstance(invalid3, int)

        # RGB components should be 0 (black)
        assert (invalid & 0xFFFFFF) == 0x000000


class TestGetTextLayoutWithHref:
    """Tests for text layout including href information."""

    def test_get_text_layout_includes_href(self):
        """Test that get_text_layout includes href for links."""
        from src.render.pipeline import RenderPipeline

        html = "<html><body><a href='https://example.com'>Click</a></body></html>"
        root = parse_html_with_styles(html)

        pipeline = RenderPipeline()
        pipeline.layout(root, 800)

        text_layout = pipeline.get_text_layout()

        # Find the link line
        link_entries = [entry for entry in text_layout if entry.get("href")]
        assert len(link_entries) > 0
        assert link_entries[0]["href"] == "https://example.com"

    def test_get_text_layout_normal_text_no_href(self):
        """Test that normal text has no href in layout."""
        from src.render.pipeline import RenderPipeline

        html = "<html><body><p>Normal text</p></body></html>"
        root = parse_html_with_styles(html)

        pipeline = RenderPipeline()
        pipeline.layout(root, 800)

        text_layout = pipeline.get_text_layout()

        # All entries should have href=None
        for entry in text_layout:
            assert entry.get("href") is None


class TestLinkDefaultStyling:
    """Tests for default link styling from CSS."""

    def test_link_default_color_in_css(self):
        """Test that default.css defines link color."""
        from pathlib import Path

        css_path = Path(__file__).parent.parent / "assets" / "default.css"
        assert css_path.exists(), "default.css should exist"

        css_content = css_path.read_text()

        # Check that 'a' selector is defined with a color
        assert "a {" in css_content or "a{" in css_content.replace(" ", "")
        assert "color:" in css_content
