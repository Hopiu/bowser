"""Tests for layout components."""

import pytest
from unittest.mock import Mock
from src.layout.document import DocumentLayout
from src.layout.block import BlockLayout, LineLayout
from src.layout.inline import TextLayout
from src.parser.html import Element, Text


class TestDocumentLayout:
    def test_document_layout_creation(self):
        node = Element("html")
        layout = DocumentLayout(node)
        assert layout.node is node
        assert layout.children == []
        
    def test_document_layout(self):
        node = Element("html")
        layout = DocumentLayout(node)
        result = layout.layout(800, 1.0)
        assert result == 800.0


class TestBlockLayout:
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


class TestLineLayout:
    def test_line_layout_creation(self):
        node = Element("span")
        layout = LineLayout(node)
        assert layout.node is node


class TestTextLayout:
    def test_text_layout_creation(self):
        node = Text("Hello")
        layout = TextLayout(node, "Hello")
        assert layout.node is node
        assert layout.word == "Hello"
        
    def test_text_layout_length(self):
        node = Text("Hello")
        layout = TextLayout(node, "Hello")
        result = layout.layout()
        assert result == 5
