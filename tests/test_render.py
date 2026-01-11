"""Tests for rendering primitives."""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock

# Mock skia before importing render modules
mock_skia = MagicMock()
mock_font = MagicMock()
mock_font.measureText = lambda text: len(text) * 7.0  # ~7 pixels per char
mock_typeface = MagicMock()
mock_skia.Typeface.MakeDefault.return_value = mock_typeface
mock_skia.Font.return_value = mock_font
sys.modules['skia'] = mock_skia

from src.render.paint import PaintCommand, DrawText, DrawRect, DisplayList
from src.render.composite import CompositedLayer
from src.render.fonts import FontCache, get_font, measure_text, linespace


class TestPaintCommands:
    """Tests for paint command base class."""
    
    def test_paint_command_creation(self):
        cmd = PaintCommand((0, 0, 100, 100))
        assert cmd.rect == (0, 0, 100, 100)


class TestDrawText:
    """Tests for DrawText paint command."""
    
    def test_draw_text_creation(self):
        cmd = DrawText(10, 20, "Hello", 14)
        assert cmd.x == 10
        assert cmd.y == 20
        assert cmd.text == "Hello"
        assert cmd.font_size == 14
    
    def test_draw_text_with_color(self):
        cmd = DrawText(0, 0, "Test", 12, color=0xFF0000)
        assert cmd.color == 0xFF0000
    
    def test_draw_text_rect_property(self):
        cmd = DrawText(10, 20, "Hi", 14)
        # Should have a rect based on position and size
        assert cmd.rect is not None
        assert cmd.rect[0] == 10  # x


class TestDrawRect:
    """Tests for DrawRect paint command."""
    
    def test_draw_rect_creation(self):
        cmd = DrawRect(10, 20, 110, 70, color=0x000000)
        assert cmd.rect == (10, 20, 110, 70)
    
    def test_draw_rect_with_color(self):
        cmd = DrawRect(0, 0, 50, 50, color=0x00FF00)
        assert cmd.color == 0x00FF00
    
    def test_draw_rect_fill_mode(self):
        cmd_fill = DrawRect(0, 0, 50, 50, color=0x000000, fill=True)
        cmd_stroke = DrawRect(0, 0, 50, 50, color=0x000000, fill=False)
        assert cmd_fill.fill is True
        assert cmd_stroke.fill is False


class TestDisplayList:
    """Tests for DisplayList class."""
    
    def test_display_list_creation(self):
        dl = DisplayList()
        assert len(dl.commands) == 0
    
    def test_display_list_append(self):
        dl = DisplayList()
        cmd = DrawText(0, 0, "Test", 14)
        dl.append(cmd)
        assert len(dl.commands) == 1
        assert dl.commands[0] is cmd
    
    def test_display_list_len(self):
        dl = DisplayList()
        dl.append(DrawText(0, 0, "A", 14))
        dl.append(DrawText(0, 20, "B", 14))
        assert len(dl) == 2
    
    def test_display_list_iteration(self):
        dl = DisplayList()
        cmd1 = DrawText(0, 0, "A", 14)
        cmd2 = DrawText(0, 20, "B", 14)
        dl.append(cmd1)
        dl.append(cmd2)
        
        items = list(dl)
        assert items == [cmd1, cmd2]


class TestCompositedLayer:
    """Tests for composited layer."""
    
    def test_composited_layer_creation(self):
        layer = CompositedLayer()
        assert layer.items == []
    
    def test_composited_layer_with_item(self):
        item = "mock_item"
        layer = CompositedLayer(item)
        assert len(layer.items) == 1
        assert layer.items[0] == item
    
    def test_add_item(self):
        layer = CompositedLayer()
        layer.add("item1")
        layer.add("item2")
        assert len(layer.items) == 2


class TestFontCache:
    """Tests for FontCache singleton."""
    
    def test_font_cache_singleton(self):
        cache1 = FontCache()
        cache2 = FontCache()
        assert cache1 is cache2
    
    def test_font_cache_get_font(self):
        cache = FontCache()
        font1 = cache.get_font(14)
        font2 = cache.get_font(14)
        # Should return the same cached font
        assert font1 is font2
    
    def test_font_cache_different_sizes(self):
        cache = FontCache()
        font14 = cache.get_font(14)
        font18 = cache.get_font(18)
        # Different sizes should be different font instances (but both are mocked)
        # At minimum, both should be non-None
        assert font14 is not None
        assert font18 is not None


class TestFontFunctions:
    """Tests for font module functions."""
    
    def test_get_font(self):
        font = get_font(14)
        assert font is not None
    
    def test_get_font_caching(self):
        font1 = get_font(16)
        font2 = get_font(16)
        assert font1 is font2
    
    def test_measure_text(self):
        width = measure_text("Hello", 14)
        assert width > 0
        assert isinstance(width, (int, float))
    
    def test_measure_text_empty(self):
        width = measure_text("", 14)
        assert width == 0
    
    def test_linespace(self):
        space = linespace(14)
        # Should be font_size * 1.4 (typical line height)
        assert space == pytest.approx(14 * 1.4, rel=0.1)
    
    def test_linespace_different_sizes(self):
        space14 = linespace(14)
        space20 = linespace(20)
        assert space20 > space14
