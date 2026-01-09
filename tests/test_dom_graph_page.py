"""Tests for DOM graph page rendering."""

import pytest
from src.templates import render_dom_graph_page
from pathlib import Path
import tempfile
import os


class TestDOMGraphPage:
    def test_render_dom_graph_page_svg(self):
        """Test rendering page with SVG graph."""
        # Create temporary SVG file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write('<svg><circle cx="50" cy="50" r="40"/></svg>')
            temp_path = f.name
        
        try:
            html = render_dom_graph_page(temp_path)
            
            assert html
            assert "DOM" in html
            assert "Visualization" in html or "Graph" in html
            assert '<svg>' in html
            assert 'circle' in html
            assert temp_path in html  # Should show file path
        finally:
            os.unlink(temp_path)
    
    def test_render_dom_graph_page_dot(self):
        """Test rendering page with DOT graph."""
        # Create temporary DOT file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
            f.write('digraph G { A -> B; }')
            temp_path = f.name
        
        try:
            html = render_dom_graph_page(temp_path)
            
            assert html
            assert "digraph G" in html
            # HTML escapes -> as &gt;
            assert ("A -> B" in html or "A -&gt; B" in html)
            assert "Graphviz" in html  # Should suggest installing graphviz
        finally:
            os.unlink(temp_path)
    
    def test_render_dom_graph_page_missing_file(self):
        """Test error handling for missing file."""
        html = render_dom_graph_page("/nonexistent/path/to/graph.svg")
        
        assert html
        assert "error" in html.lower() or "not found" in html.lower()
    
    def test_render_dom_graph_page_has_legend(self):
        """Test that SVG page includes color legend."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write('<svg><rect/></svg>')
            temp_path = f.name
        
        try:
            html = render_dom_graph_page(temp_path)
            
            # Should have legend explaining colors
            assert 'legend' in html.lower() or 'color' in html.lower()
        finally:
            os.unlink(temp_path)
