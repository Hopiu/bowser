"""Tests for HTML parsing functionality."""

import pytest
from src.parser.html import parse_html, Text, Element


class TestParseHTML:
    def test_parse_simple_text(self):
        html = "<html><body>Hello World</body></html>"
        root = parse_html(html)
        
        assert isinstance(root, Element)
        assert root.tag == "html"
        assert len(root.children) == 1
        
        body = root.children[0]
        assert body.tag == "body"
        assert len(body.children) == 1
        
        text = body.children[0]
        assert isinstance(text, Text)
        assert "Hello World" in text.text
        
    def test_parse_strips_tags(self):
        html = "<html><body><p>Hello</p><div>World</div></body></html>"
        root = parse_html(html)
        
        body = root.children[0]
        text = body.children[0]
        assert "Hello" in text.text
        assert "World" in text.text
        
    def test_parse_removes_script_tags(self):
        html = "<html><body>Visible<script>alert('bad')</script>Text</body></html>"
        root = parse_html(html)
        
        body = root.children[0]
        text = body.children[0]
        assert "Visible" in text.text
        assert "Text" in text.text
        assert "alert" not in text.text
        assert "script" not in text.text.lower()
        
    def test_parse_removes_style_tags(self):
        html = "<html><body>Text<style>body{color:red;}</style>More</body></html>"
        root = parse_html(html)
        
        body = root.children[0]
        text = body.children[0]
        assert "Text" in text.text
        assert "More" in text.text
        assert "color" not in text.text
        
    def test_parse_decodes_entities(self):
        html = "<html><body>&lt;div&gt; &amp; &quot;test&quot;</body></html>"
        root = parse_html(html)
        
        body = root.children[0]
        text = body.children[0]
        assert "<div>" in text.text
        assert "&" in text.text
        assert '"test"' in text.text
        
    def test_parse_normalizes_whitespace(self):
        html = "<html><body>Hello    \n\n   World</body></html>"
        root = parse_html(html)
        
        body = root.children[0]
        text = body.children[0]
        # Multiple whitespace should be collapsed
        assert "Hello World" in text.text
        
    def test_parse_empty_document(self):
        html = "<html><body></body></html>"
        root = parse_html(html)
        
        assert isinstance(root, Element)
        assert root.tag == "html"
        body = root.children[0]
        assert body.tag == "body"
        # Empty body should have no text children
        assert len(body.children) == 0
