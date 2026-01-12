"""Painting primitives using Skia."""

import skia
from .fonts import get_font


class PaintCommand:
    """Base class for paint commands."""

    def __init__(self, rect):
        self.rect = rect  # (x1, y1, x2, y2) bounding box

    def execute(self, canvas: skia.Canvas):
        """Execute this paint command on the canvas."""
        raise NotImplementedError


class DrawText(PaintCommand):
    """Command to draw text."""

    def __init__(self, x: float, y: float, text: str, font_size: int, color=None):
        self.x = x
        self.y = y
        self.text = text
        self.font_size = font_size
        self.color = color or skia.ColorBLACK
        self._font = get_font(font_size)
        width = self._font.measureText(text)
        super().__init__((x, y - font_size, x + width, y))

    def execute(self, canvas: skia.Canvas, paint: skia.Paint = None):
        """Draw the text on the canvas."""
        if paint is None:
            paint = skia.Paint()
            paint.setAntiAlias(True)
            paint.setColor(self.color)
        canvas.drawString(self.text, self.x, self.y, self._font, paint)


class DrawRect(PaintCommand):
    """Command to draw a rectangle."""

    def __init__(self, x1: float, y1: float, x2: float, y2: float, color, fill: bool = True):
        super().__init__((x1, y1, x2, y2))
        self.color = color
        self.fill = fill

    def execute(self, canvas: skia.Canvas, paint: skia.Paint = None):
        """Draw the rectangle on the canvas."""
        if paint is None:
            paint = skia.Paint()
            paint.setColor(self.color)
            paint.setStyle(skia.Paint.kFill_Style if self.fill else skia.Paint.kStroke_Style)
        rect = skia.Rect.MakeLTRB(*self.rect)
        canvas.drawRect(rect, paint)


class DisplayList:
    """A list of paint commands to execute."""

    def __init__(self):
        self.commands = []

    def append(self, command: PaintCommand):
        """Add a paint command."""
        self.commands.append(command)

    def execute(self, canvas: skia.Canvas, paint: skia.Paint = None):
        """Execute all commands on the canvas."""
        for cmd in self.commands:
            cmd.execute(canvas, paint)

    def __len__(self):
        return len(self.commands)

    def __iter__(self):
        return iter(self.commands)
