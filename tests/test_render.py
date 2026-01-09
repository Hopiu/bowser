"""Tests for rendering primitives."""

import pytest
from src.render.paint import PaintCommand, DrawText
from src.render.composite import CompositedLayer
from src.render.fonts import get_font, linespace


class TestPaintCommands:
    def test_paint_command_creation(self):
        cmd = PaintCommand((0, 0, 100, 100))
        assert cmd.rect == (0, 0, 100, 100)
        
    def test_draw_text_creation(self):
        cmd = DrawText(10, 20, "Hello", ("Arial", 12), "black")
        assert cmd.text == "Hello"
        assert cmd.font == ("Arial", 12)
        assert cmd.color == "black"


class TestCompositedLayer:
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


class TestFonts:
    def test_get_font(self):
        font = get_font(14)
        assert font == (14, "normal", "normal")
        
    def test_get_font_with_weight(self):
        font = get_font(16, weight="bold")
        assert font == (16, "bold", "normal")
        
    def test_get_font_with_style(self):
        font = get_font(12, style="italic")
        assert font == (12, "normal", "italic")
        
    def test_linespace(self):
        font = (14, "normal", "normal")
        space = linespace(font)
        assert space == int(14 * 1.2)
