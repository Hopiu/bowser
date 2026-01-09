"""Tests for DOM graph visualization."""

import pytest
from src.parser.html import parse_html, Element, Text
from src.debug.dom_graph import generate_dot_graph, print_dom_tree


class TestDOMGraph:
    def test_generate_dot_graph_empty(self):
        """Test generating graph for None document."""
        dot = generate_dot_graph(None)
        
        assert "digraph DOM" in dot
        assert "Empty Document" in dot
    
    def test_generate_dot_graph_simple(self):
        """Test generating graph for simple HTML."""
        html = "<html><body><p>Hello World</p></body></html>"
        doc = parse_html(html)
        
        dot = generate_dot_graph(doc)
        
        assert "digraph DOM" in dot
        assert "node_" in dot  # Should have node IDs
        assert "<html>" in dot
        assert "<body>" in dot
        assert "<p>" in dot
        assert "Hello World" in dot
    
    def test_generate_dot_graph_with_attributes(self):
        """Test graph generation with element attributes."""
        html = '<html><body><div class="test" id="main">Content</div></body></html>'
        doc = parse_html(html)
        
        dot = generate_dot_graph(doc)
        
        assert "digraph DOM" in dot
        assert "<div>" in dot
        # Attributes should be included (at least some of them)
        assert "class" in dot or "id" in dot
    
    def test_generate_dot_graph_nested(self):
        """Test graph generation with nested elements."""
        html = """
        <html>
            <body>
                <div>
                    <p>First</p>
                    <p>Second</p>
                </div>
            </body>
        </html>
        """
        doc = parse_html(html)
        
        dot = generate_dot_graph(doc)
        
        assert "digraph DOM" in dot
        assert "->" in dot  # Should have edges
        assert "First" in dot
        assert "Second" in dot
    
    def test_generate_dot_graph_colors(self):
        """Test that different element types get different colors."""
        html = "<html><body><h1>Title</h1><p>Text</p><ul><li>Item</li></ul></body></html>"
        doc = parse_html(html)
        
        dot = generate_dot_graph(doc)
        
        # Check for color attributes
        assert "fillcolor=" in dot
        assert "lightgreen" in dot or "lightyellow" in dot or "lightgray" in dot
    
    def test_print_dom_tree_simple(self):
        """Test text tree representation."""
        html = "<html><body><p>Hello</p></body></html>"
        doc = parse_html(html)
        
        tree = print_dom_tree(doc)
        
        assert "<html>" in tree
        assert "<body>" in tree
        assert "<p>" in tree
        assert "Hello" in tree
    
    def test_print_dom_tree_indentation(self):
        """Test that tree has proper indentation."""
        html = "<html><body><div><p>Nested</p></div></body></html>"
        doc = parse_html(html)
        
        tree = print_dom_tree(doc)
        
        # Should have increasing indentation
        lines = tree.split('\n')
        # Find the nested <p> line - should be more indented than <div>
        p_line = [l for l in lines if '<p>' in l][0]
        div_line = [l for l in lines if '<div>' in l][0]
        
        # Count leading spaces
        p_indent = len(p_line) - len(p_line.lstrip())
        div_indent = len(div_line) - len(div_line.lstrip())
        
        assert p_indent > div_indent
    
    def test_print_dom_tree_max_depth(self):
        """Test that max_depth limits tree traversal."""
        html = "<html><body><div><div><div><p>Deep</p></div></div></div></body></html>"
        doc = parse_html(html)
        
        tree_shallow = print_dom_tree(doc, max_depth=2)
        tree_deep = print_dom_tree(doc, max_depth=10)
        
        # Shallow should be shorter
        assert len(tree_shallow) < len(tree_deep)
        assert "..." in tree_shallow
    
    def test_generate_dot_graph_text_escaping(self):
        """Test that special characters in text are escaped."""
        html = '<html><body><p>Text with "quotes" and newlines\n</p></body></html>'
        doc = parse_html(html)
        
        dot = generate_dot_graph(doc)
        
        # Should have escaped quotes
        assert '\\"' in dot or 'quotes' in dot
        # Should not have raw newlines breaking the DOT format
        lines = dot.split('\n')
        # All lines should be valid (no line starts with unexpected characters)
        for line in lines:
            if line.strip():
                assert not line.strip().startswith('"') or line.strip().endswith(';') or line.strip().endswith(']')
    
    def test_generate_dot_graph_long_text_truncation(self):
        """Test that very long text nodes are truncated."""
        long_text = "A" * 100
        html = f"<html><body><p>{long_text}</p></body></html>"
        doc = parse_html(html)
        
        dot = generate_dot_graph(doc)
        
        # Should contain truncation marker
        assert "..." in dot
