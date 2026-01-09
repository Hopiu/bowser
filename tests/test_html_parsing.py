"""Tests for HTML parsing functionality."""

import pytest
from src.parser.html import parse_html, Text, Element


def collect_text(node):
    texts = []
    if isinstance(node, Text):
        texts.append(node.text)
    if hasattr(node, "children"):
        for child in node.children:
            texts.extend(collect_text(child))
    return texts


class TestParseHTML:
    def test_parse_simple_text(self):
        html = "<html><body>Hello World</body></html>"
        root = parse_html(html)
        
        assert isinstance(root, Element)
        assert root.tag == "html"
        assert len(root.children) == 1
        
        body = root.children[0]
        assert body.tag == "body"
        texts = collect_text(body)
        joined = " ".join(texts)
        assert "Hello World" in joined
        
    def test_parse_strips_tags(self):
        html = "<html><body><p>Hello</p><div>World</div></body></html>"
        root = parse_html(html)
        
        body = root.children[0]
        joined = " ".join(collect_text(body))
        assert "Hello" in joined
        assert "World" in joined
        
    def test_parse_removes_script_tags(self):
        html = "<html><body>Visible<script>alert('bad')</script>Text</body></html>"
        root = parse_html(html)
        
        body = root.children[0]
        joined = " ".join(collect_text(body))
        assert "Visible" in joined
        assert "Text" in joined
        assert "alert" not in joined
        assert "script" not in joined.lower()
        
    def test_parse_removes_style_tags(self):
        html = "<html><body>Text<style>body{color:red;}</style>More</body></html>"
        root = parse_html(html)
        
        body = root.children[0]
        joined = " ".join(collect_text(body))
        assert "Text" in joined
        assert "More" in joined
        assert "color" not in joined
        
    def test_parse_decodes_entities(self):
        html = "<html><body>&lt;div&gt; &amp; &quot;test&quot;</body></html>"
        root = parse_html(html)
        
        body = root.children[0]
        joined = " ".join(collect_text(body))
        assert "<div>" in joined
        assert "&" in joined
        assert '"test"' in joined
        
    def test_parse_normalizes_whitespace(self):
        html = "<html><body>Hello    \n\n   World</body></html>"
        root = parse_html(html)
        
        body = root.children[0]
        joined = " ".join(collect_text(body))
        # Multiple whitespace should be collapsed
        assert "Hello World" in joined
        
    def test_parse_empty_document(self):
        html = "<html><body></body></html>"
        root = parse_html(html)
        
        assert isinstance(root, Element)
        assert root.tag == "html"
        body = root.children[0]
        assert body.tag == "body"
        # Empty body should have no text children
        assert len(collect_text(body)) == 0
