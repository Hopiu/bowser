"""Integration tests for CSS styling system."""

import pytest
from src.parser.html import parse_html_with_styles
from src.layout.document import DocumentLayout


class TestStyleIntegration:
    """Test end-to-end CSS parsing and layout integration."""

    def test_parse_with_style_tag(self):
        html = """
        <html>
        <head>
            <style>
                p { color: red; font-size: 18px; }
            </style>
        </head>
        <body>
            <p>Hello World</p>
        </body>
        </html>
        """
        root = parse_html_with_styles(html)

        # Find the p element
        p_elem = None
        for child in root.children:
            if hasattr(child, "tag") and child.tag == "body":
                for grandchild in child.children:
                    if hasattr(grandchild, "tag") and grandchild.tag == "p":
                        p_elem = grandchild
                        break

        assert p_elem is not None
        assert hasattr(p_elem, "computed_style")
        assert p_elem.computed_style.get("color") == "red"
        assert p_elem.computed_style.get("font-size") == "18px"

    def test_inline_style_override(self):
        html = """
        <html>
        <body>
            <p style="color: blue; font-size: 20px">Styled paragraph</p>
        </body>
        </html>
        """
        root = parse_html_with_styles(html)

        # Find the p element
        for child in root.children:
            if hasattr(child, "tag") and child.tag == "body":
                for grandchild in child.children:
                    if hasattr(grandchild, "tag") and grandchild.tag == "p":
                        p_elem = grandchild
                        assert p_elem.computed_style.get("color") == "blue"
                        assert p_elem.computed_style.get("font-size") == "20px"
                        return

        pytest.fail("P element not found")

    def test_cascade_priority(self):
        html = """
        <html>
        <head>
            <style>
                p { color: red; }
                .highlight { color: green; }
                #special { color: blue; }
            </style>
        </head>
        <body>
            <p>Tag only</p>
            <p class="highlight">With class</p>
            <p id="special" class="highlight">With ID</p>
            <p id="special" class="highlight" style="color: purple">With inline</p>
        </body>
        </html>
        """
        root = parse_html_with_styles(html)

        # Find body
        body = None
        for child in root.children:
            if hasattr(child, "tag") and child.tag == "body":
                body = child
                break

        assert body is not None
        paragraphs = [c for c in body.children if hasattr(c, "tag") and c.tag == "p"]
        assert len(paragraphs) == 4

        # Check cascade
        assert paragraphs[0].computed_style.get("color") == "red"  # Tag only
        assert paragraphs[1].computed_style.get("color") == "green"  # Class wins
        assert paragraphs[2].computed_style.get("color") == "blue"  # ID wins
        assert paragraphs[3].computed_style.get("color") == "purple"  # Inline wins

    def test_inheritance(self):
        html = """
        <html>
        <head>
            <style>
                body { color: blue; font-size: 16px; }
            </style>
        </head>
        <body>
            <div>
                <p>Nested paragraph</p>
            </div>
        </body>
        </html>
        """
        root = parse_html_with_styles(html)

        # Find the nested p element
        for child in root.children:
            if hasattr(child, "tag") and child.tag == "body":
                for grandchild in child.children:
                    if hasattr(grandchild, "tag") and grandchild.tag == "div":
                        for ggchild in grandchild.children:
                            if hasattr(ggchild, "tag") and ggchild.tag == "p":
                                # Should inherit color from body
                                assert ggchild.computed_style.get("color") == "blue"
                                # Font-size may be set by default.css
                                assert ggchild.computed_style.get("font-size") != ""
                                return

        pytest.fail("Nested p element not found")

    def test_layout_uses_styles(self):
        html = """
        <html>
        <head>
            <style>
                h1 { font-size: 40px; margin-top: 30px; margin-bottom: 30px; }
                p { font-size: 20px; margin-top: 10px; margin-bottom: 10px; }
            </style>
        </head>
        <body>
            <h1>Title</h1>
            <p>Paragraph</p>
        </body>
        </html>
        """
        root = parse_html_with_styles(html)

        # Create layout
        layout = DocumentLayout(root)
        lines = layout.layout(800)
        # H1 should use custom font size
        assert lines[0].font_size == 40

        # P should use custom font size
        assert lines[1].font_size == 20

    def test_multiple_classes(self):
        html = """
        <html>
        <head>
            <style>
                .big { font-size: 24px; }
                .red { color: red; }
            </style>
        </head>
        <body>
            <p class="big red">Multiple classes</p>
        </body>
        </html>
        """
        root = parse_html_with_styles(html)

        # Find the p element
        for child in root.children:
            if hasattr(child, "tag") and child.tag == "body":
                for grandchild in child.children:
                    if hasattr(grandchild, "tag") and grandchild.tag == "p":
                        # Should match both classes
                        assert grandchild.computed_style.get("font-size") == "24px"
                        assert grandchild.computed_style.get("color") == "red"
                        return

        pytest.fail("P element not found")

    def test_default_styles_applied(self):
        html = """
        <html>
        <body>
            <h1>Heading</h1>
            <p>Paragraph</p>
            <a href="#">Link</a>
        </body>
        </html>
        """
        root = parse_html_with_styles(html)

        # Find elements
        body = None
        for child in root.children:
            if hasattr(child, "tag") and child.tag == "body":
                body = child
                break

        assert body is not None

        h1 = next((c for c in body.children if hasattr(c, "tag") and c.tag == "h1"), None)
        p = next((c for c in body.children if hasattr(c, "tag") and c.tag == "p"), None)
        a = next((c for c in body.children if hasattr(c, "tag") and c.tag == "a"), None)

        # Check default styles from default.css
        assert h1 is not None
        # Font-size from default.css is 2.5rem
        assert h1.computed_style.get("font-size") == "2.5rem"
        assert h1.computed_style.get("font-weight") == "600"

        assert p is not None
        assert p.computed_style.get("display") == "block"

        assert a is not None
        # Link color from default.css
        assert a.computed_style.get("color") == "#0066cc"
        assert a.computed_style.get("text-decoration") == "none"

    def test_no_styles_when_disabled(self):
        html = """
        <html>
        <head>
            <style>
                p { color: red; }
            </style>
        </head>
        <body>
            <p>Test</p>
        </body>
        </html>
        """
        root = parse_html_with_styles(html, apply_styles=False)

        # Find the p element
        for child in root.children:
            if hasattr(child, "tag") and child.tag == "body":
                for grandchild in child.children:
                    if hasattr(grandchild, "tag") and grandchild.tag == "p":
                        # Should not have computed_style when disabled
                        assert not hasattr(grandchild, "computed_style")
                        return

        pytest.fail("P element not found")
