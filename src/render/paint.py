"""Painting primitives (stubs)."""


class PaintCommand:
    def __init__(self, rect):
        self.rect = rect


class DrawText(PaintCommand):
    def __init__(self, x1, y1, text, font, color):
        super().__init__((x1, y1, x1, y1))
        self.text = text
        self.font = font
        self.color = color

    def execute(self, canvas):
        # Placeholder: integrate with Skia/Cairo later
        pass
