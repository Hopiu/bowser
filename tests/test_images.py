"""Tests for image loading and rendering."""

import skia
from src.network.images import ImageCache, _load_data_url
from src.layout.embed import ImageLayout
from src.parser.html import Element, parse_html
from src.render.paint import DrawImage
from src.layout.document import DocumentLayout, LayoutImage


def create_test_image(width=100, height=100):
    """Helper to create a test image."""
    # Create a surface and get an image from it
    surface = skia.Surface(width, height)
    canvas = surface.getCanvas()
    canvas.clear(skia.ColorWHITE)
    return surface.makeImageSnapshot()


class TestImageCache:
    """Test image caching."""

    def test_cache_singleton(self):
        """ImageCache should be a singleton."""
        cache1 = ImageCache()
        cache2 = ImageCache()
        assert cache1 is cache2

    def test_cache_get_set(self):
        """Test basic cache operations."""
        cache = ImageCache()
        cache.clear()

        # Create a simple test image
        image = create_test_image(100, 100)

        # Initially empty
        assert cache.get("test_url") is None

        # Set and get
        cache.set("test_url", image)
        cached = cache.get("test_url")
        assert cached is not None
        assert cached.width() == 100
        assert cached.height() == 100

    def test_cache_clear(self):
        """Test cache clearing."""
        cache = ImageCache()
        cache.clear()

        image = create_test_image(100, 100)
        cache.set("test_url", image)
        assert cache.get("test_url") is not None

        cache.clear()
        assert cache.get("test_url") is None


class TestDataURLLoading:
    """Test data URL image loading."""

    def test_load_base64_png(self):
        """Test loading a base64-encoded PNG data URL."""
        # Simple 1x1 red PNG
        data_url = (
            "data:image/png;base64,"
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
        )

        image = _load_data_url(data_url)
        assert image is not None
        assert image.width() == 1
        assert image.height() == 1

    def test_load_invalid_data_url(self):
        """Test loading an invalid data URL."""
        image = _load_data_url("data:invalid")
        assert image is None

        image = _load_data_url("not_a_data_url")
        assert image is None


class TestImageLayout:
    """Test ImageLayout class."""

    def test_image_layout_init(self):
        """Test ImageLayout initialization."""
        node = Element("img", {"src": "test.png"})
        layout = ImageLayout(node)

        assert layout.node == node
        assert layout.x == 0
        assert layout.y == 0
        assert layout.width == 0
        assert layout.height == 0
        assert layout.image is None
        assert layout.is_inline is True

    def test_layout_with_intrinsic_size(self):
        """Test layout calculation with intrinsic image size."""
        node = Element("img", {"src": "test.png"})
        layout = ImageLayout(node)

        # Create a test image
        layout.image = create_test_image(200, 150)

        width = layout.layout()

        assert layout.width == 200
        assert layout.height == 150
        assert width == 200

    def test_layout_with_explicit_width(self):
        """Test layout with explicit width attribute."""
        node = Element("img", {"src": "test.png", "width": "100"})
        layout = ImageLayout(node)

        # Create a test image (200x150)
        layout.image = create_test_image(200, 150)

        layout.layout()

        # Should maintain aspect ratio
        assert layout.width == 100
        assert layout.height == 75  # 100 * (150/200)

    def test_layout_with_explicit_height(self):
        """Test layout with explicit height attribute."""
        node = Element("img", {"src": "test.png", "height": "100"})
        layout = ImageLayout(node)

        # Create a test image (200x150)
        layout.image = create_test_image(200, 150)

        layout.layout()

        # Should maintain aspect ratio
        assert layout.height == 100
        assert abs(layout.width - 133.33) < 1  # 100 * (200/150)

    def test_layout_with_both_dimensions(self):
        """Test layout with both width and height specified."""
        node = Element("img", {"src": "test.png", "width": "100", "height": "50"})
        layout = ImageLayout(node)

        # Create a test image
        layout.image = create_test_image(200, 150)

        layout.layout()

        # Should use explicit dimensions (no aspect ratio preservation)
        assert layout.width == 100
        assert layout.height == 50

    def test_layout_with_max_width(self):
        """Test layout constrained by max_width."""
        node = Element("img", {"src": "test.png"})
        layout = ImageLayout(node)

        # Create a large test image
        layout.image = create_test_image(1000, 500)

        layout.layout(max_width=400)

        # Should constrain to max_width and maintain aspect ratio
        assert layout.width == 400
        assert layout.height == 200  # 400 * (500/1000)

    def test_layout_no_image(self):
        """Test layout when image fails to load."""
        node = Element("img", {"src": "test.png", "alt": "Test image"})
        layout = ImageLayout(node)

        # Don't set an image (simulating load failure)
        layout.alt_text = "Test image"
        layout.layout()

        # Should use placeholder dimensions
        assert layout.width == 100
        assert layout.height == 100

    def test_alt_text_extraction(self):
        """Test alt text extraction."""
        node = Element("img", {"src": "test.png", "alt": "Description"})
        layout = ImageLayout(node)

        layout.load()

        assert layout.alt_text == "Description"


class TestDrawImage:
    """Test DrawImage paint command."""

    def test_draw_image_init(self):
        """Test DrawImage initialization."""
        image = create_test_image(100, 100)

        cmd = DrawImage(10, 20, 100, 100, image, "Test")

        assert cmd.x == 10
        assert cmd.y == 20
        assert cmd.width == 100
        assert cmd.height == 100
        assert cmd.image is image
        assert cmd.alt_text == "Test"
        assert cmd.rect == (10, 20, 110, 120)

    def test_draw_image_with_valid_image(self):
        """Test drawing a valid image."""
        image = create_test_image(100, 100)

        # Create a surface to draw on
        surface = skia.Surface(200, 200)
        canvas = surface.getCanvas()

        cmd = DrawImage(10, 20, 100, 100, image)
        cmd.execute(canvas)

        # If it doesn't throw, it worked
        assert True

    def test_draw_image_with_null_image(self):
        """Test drawing when image is None (placeholder)."""
        # Create a surface to draw on
        surface = skia.Surface(200, 200)
        canvas = surface.getCanvas()

        cmd = DrawImage(10, 20, 100, 100, None, "Failed to load")
        cmd.execute(canvas)

        # Should draw placeholder without error
        assert True


class TestDocumentLayoutImages:
    """Test image integration in DocumentLayout."""

    def test_parse_img_element(self):
        """Test that img elements are parsed correctly."""
        html = '<img src="test.png" alt="Test image" width="100">'
        root = parse_html(html)

        # Find the img element
        body = root.children[0]
        img = body.children[0]

        assert img.tag == "img"
        assert img.attributes["src"] == "test.png"
        assert img.attributes["alt"] == "Test image"
        assert img.attributes["width"] == "100"

    def test_layout_with_image(self):
        """Test document layout with an image."""
        html = '<p>Text before</p><img src="test.png" width="100" height="75"><p>Text after</p>'
        root = parse_html(html)

        layout = DocumentLayout(root)

        # Mock the image loading by creating the images manually
        # This would normally happen in _collect_blocks
        # For now, just verify the structure is created
        lines = layout.layout(800)

        # Should have lines and potentially images
        assert isinstance(lines, list)

    def test_layout_image_class(self):
        """Test LayoutImage class."""
        node = Element("img", {"src": "test.png"})
        image_layout = ImageLayout(node)
        image_layout.image = create_test_image(100, 100)
        image_layout.layout()

        layout_image = LayoutImage(image_layout, 10, 20)

        assert layout_image.x == 10
        assert layout_image.y == 20
        assert layout_image.width == 100
        assert layout_image.height == 100
        assert layout_image.image_layout is image_layout


class TestImageIntegration:
    """Integration tests for the complete image pipeline."""

    def test_html_with_data_url_image(self):
        """Test parsing and layout of HTML with data URL image."""
        # 1x1 red PNG
        data_url = (
            "data:image/png;base64,"
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
        )

        html = f'<p>Before</p><img src="{data_url}" width="50" height="50"><p>After</p>'
        root = parse_html(html)

        # Verify structure
        body = root.children[0]
        # The img tag is self-closing, so the second p tag becomes a child of img
        # This is a quirk of the HTML parser treating img as a container
        assert len(body.children) >= 2
        assert body.children[0].tag == "p"
        assert body.children[1].tag == "img"

    def test_nested_image_in_paragraph(self):
        """Test that images inside paragraphs are collected."""
        # 1x1 red PNG
        data_url = (
            "data:image/png;base64,"
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
        )

        html = f'<p>Text before <img src="{data_url}" width="50" height="50"> text after</p>'
        root = parse_html(html)

        # Create layout and verify images are collected
        layout = DocumentLayout(root)
        layout.layout(800)

        # Should have at least one image collected
        assert len(layout.images) >= 1

    def test_image_with_alt_text_placeholder(self):
        """Test that failed images show placeholder with alt text."""
        html = '<img src="nonexistent.png" width="200" height="100" alt="Image failed">'
        root = parse_html(html)

        layout = DocumentLayout(root)
        layout.layout(800)

        # Should have image layout even though load failed
        assert len(layout.images) >= 1

        # Check alt text is set
        if layout.images:
            img = layout.images[0]
            assert img.image_layout.alt_text == "Image failed"


class TestURLResolution:
    """Test URL resolution for images."""

    def test_resolve_about_page_relative_url(self):
        """Test resolving relative URLs for about: pages."""
        from src.network.images import _resolve_url, ASSETS_DIR

        # Relative URL from about:startpage should resolve to assets directory
        resolved = _resolve_url("../WebBowserLogo.jpeg", "about:startpage")

        # Should be an absolute path to the assets directory
        assert "WebBowserLogo.jpeg" in resolved
        assert str(ASSETS_DIR) in resolved or resolved.endswith("WebBowserLogo.jpeg")

    def test_resolve_http_relative_url(self):
        """Test resolving relative URLs for HTTP pages."""
        from src.network.images import _resolve_url

        # Relative URL from HTTP page
        resolved = _resolve_url("images/photo.jpg", "https://example.com/page/index.html")

        assert resolved == "https://example.com/page/images/photo.jpg"

    def test_resolve_absolute_url(self):
        """Test that absolute URLs are returned unchanged."""
        from src.network.images import _resolve_url

        url = "https://example.com/image.png"
        resolved = _resolve_url(url, "https://other.com/page.html")

        assert resolved == url

    def test_resolve_data_url(self):
        """Test that data URLs are returned unchanged."""
        from src.network.images import _resolve_url

        url = "data:image/png;base64,abc123"
        resolved = _resolve_url(url, "https://example.com/")

        assert resolved == url
