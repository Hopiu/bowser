# ruff: noqa: E402
"""Tests for layout components."""

import pytest
import sys
from unittest.mock import MagicMock

# Mock skia before importing layout modules
mock_skia = MagicMock()
mock_font = MagicMock()
mock_font.measureText = lambda text: len(text) * 7.0  # ~7 pixels per char
mock_typeface = MagicMock()
mock_skia.Typeface.MakeDefault.return_value = mock_typeface
mock_skia.Font.return_value = mock_font
sys.modules['skia'] = mock_skia

from src.layout.document import DocumentLayout, LayoutLine, LayoutBlock
from src.layout.block import BlockLayout, LineLayout, build_block_layout
from src.layout.inline import TextLayout, InlineLayout
from src.parser.html import Element, Text


class TestLayoutLine:
    """Tests for LayoutLine class."""

    def test_layout_line_creation(self):
        line = LayoutLine("Hello", 20, 100, 14)
        assert line.text == "Hello"
        assert line.x == 20
        assert line.y == 100
        assert line.font_size == 14

    def test_layout_line_with_char_positions(self):
        char_positions = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0]
        line = LayoutLine("Hello", 20, 100, 14, char_positions)
        assert line.char_positions == char_positions

    def test_layout_line_height(self):
        line = LayoutLine("Test", 0, 0, 14)
        # Height should be based on linespace (font_size * 1.4)
        assert line.height == pytest.approx(14 * 1.4, rel=0.1)


class TestLayoutBlock:
    """Tests for LayoutBlock class."""

    def test_layout_block_creation(self):
        block = LayoutBlock("p")
        assert block.tag == "p"
        assert block.block_type == "block"
        assert block.lines == []

    def test_layout_block_with_type(self):
        block = LayoutBlock("li", "list-item")
        assert block.block_type == "list-item"


class TestDocumentLayout:
    """Tests for DocumentLayout class."""

    def test_document_layout_creation(self):
        node = Element("html")
        layout = DocumentLayout(node)
        assert layout.node is node
        assert layout.blocks == []
        assert layout.lines == []

    def test_document_layout_finds_body(self):
        # Create HTML structure: html > body > p
        html = Element("html")
        body = Element("body")
        p = Element("p")
        p.children = [Text("Hello world")]
        body.children = [p]
        html.children = [body]

        layout = DocumentLayout(html)
        lines = layout.layout(800)

        assert len(lines) > 0
        assert any("Hello world" in line.text for line in lines)

    def test_document_layout_returns_empty_without_body(self):
        node = Element("div")
        node.children = []
        layout = DocumentLayout(node)
        lines = layout.layout(800)
        assert lines == []

    def test_document_layout_handles_headings(self):
        body = Element("body")
        h1 = Element("h1")
        h1.children = [Text("Title")]
        body.children = [h1]

        layout = DocumentLayout(body)
        lines = layout.layout(800)

        assert len(lines) == 1
        assert lines[0].text == "Title"
        assert lines[0].font_size == 24  # h1 font size

    def test_document_layout_handles_paragraphs(self):
        body = Element("body")
        p = Element("p")
        p.children = [Text("Paragraph text")]
        body.children = [p]

        layout = DocumentLayout(body)
        lines = layout.layout(800)

        assert len(lines) == 1
        assert lines[0].text == "Paragraph text"
        assert lines[0].font_size == 14  # p font size

    def test_document_layout_handles_lists(self):
        body = Element("body")
        ul = Element("ul")
        li = Element("li")
        li.children = [Text("List item")]
        ul.children = [li]
        body.children = [ul]

        layout = DocumentLayout(body)
        lines = layout.layout(800)

        assert len(lines) == 1
        assert "•" in lines[0].text  # Bullet prefix
        assert "List item" in lines[0].text

    def test_document_layout_word_wrapping(self):
        body = Element("body")
        p = Element("p")
        # Long text that should wrap
        p.children = [
            Text(
                "This is a very long paragraph that should wrap to multiple lines "
                "when the width is narrow enough"
            )
        ]
        body.children = [p]

        layout = DocumentLayout(body)
        lines = layout.layout(200)  # Narrow width to force wrapping

        assert len(lines) > 1  # Should wrap to multiple lines

    def test_document_layout_char_positions(self):
        body = Element("body")
        p = Element("p")
        p.children = [Text("Hello")]
        body.children = [p]

        layout = DocumentLayout(body)
        lines = layout.layout(800)

        assert len(lines) == 1
        # char_positions should have len(text) + 1 entries (including start at 0)
        assert len(lines[0].char_positions) == 6  # "Hello" = 5 chars + 1
        assert lines[0].char_positions[0] == 0.0


class TestBlockLayout:
    """Tests for BlockLayout class."""

    def test_block_layout_creation(self):
        node = Element("div")
        layout = BlockLayout(node)
        assert layout.node is node
        assert layout.children == []

    def test_block_layout_with_parent(self):
        parent_node = Element("body")
        child_node = Element("div")
        parent_layout = BlockLayout(parent_node)
        child_layout = BlockLayout(child_node, parent=parent_layout)
        assert child_layout.parent is parent_layout

    def test_block_layout_stores_dimensions(self):
        node = Element("div")
        layout = BlockLayout(node)
        layout.x = 10
        layout.y = 20
        layout.width = 100
        layout.height = 50
        assert layout.x == 10
        assert layout.y == 20
        assert layout.width == 100
        assert layout.height == 50


class TestLineLayout:
    """Tests for LineLayout class."""

    def test_line_layout_creation(self):
        layout = LineLayout()
        assert layout.words == []
        assert layout.x == 0
        assert layout.y == 0

    def test_line_layout_add_word(self):
        layout = LineLayout()
        layout.add_word("Hello", 0, 14)
        layout.add_word("World", 50, 14)
        assert len(layout.words) == 2


class TestTextLayout:
    """Tests for TextLayout class."""

    def test_text_layout_creation(self):
        node = Text("Hello")
        layout = TextLayout(node, "Hello")
        assert layout.node is node
        assert layout.word == "Hello"

    def test_text_layout_layout_returns_width(self):
        node = Text("Test")
        layout = TextLayout(node, "Test")
        width = layout.layout(14)
        assert width > 0

    def test_text_layout_dimensions(self):
        node = Text("Hi")
        layout = TextLayout(node, "Hi")
        layout.x = 5
        layout.y = 10
        assert layout.x == 5
        assert layout.y == 10


class TestInlineLayout:
    """Tests for InlineLayout class."""

    def test_inline_layout_creation(self):
        node = Text("Hello")
        layout = InlineLayout(node)
        assert layout.node is node
        assert layout.children == []

    def test_inline_layout_add_word(self):
        node = Text("Hello World")
        layout = InlineLayout(node)
        layout.add_word("Hello", 14)
        layout.add_word("World", 14)
        assert len(layout.children) == 2

    def test_inline_layout_layout(self):
        node = Text("Hello World")
        layout = InlineLayout(node)
        layout.add_word("Hello", 14)
        layout.add_word("World", 14)
        lines = layout.layout(0, 0, 1000, 14)
        # Both words should fit on one line with wide width
        assert len(lines) == 1


class TestBuildBlockLayout:
    """Tests for build_block_layout factory function."""

    def test_build_block_layout_from_element(self):
        node = Element("p")
        node.children = [Text("Test paragraph")]
        result = build_block_layout(node)
        assert result is not None
        assert result.node is node
        assert result.font_size == 14

    def test_build_block_layout_heading(self):
        node = Element("h1")
        node.children = [Text("Heading")]
        result = build_block_layout(node, font_size=24)
        assert result.font_size == 24

    def test_build_block_layout_list_item(self):
        node = Element("li")
        node.children = [Text("Item")]
        result = build_block_layout(node, block_type="list-item", bullet=True)
        assert result.block_type == "list-item"
