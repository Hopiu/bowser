"""Painting primitives using Skia."""

import logging
import skia
from .fonts import get_font

logger = logging.getLogger("bowser.paint")


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


class DrawImage(PaintCommand):
    """Command to draw an image."""

    def __init__(self, x: float, y: float, width: float, height: float,
                 image: skia.Image, alt_text: str = ""):
        super().__init__((x, y, x + width, y + height))
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.image = image
        self.alt_text = alt_text

    def execute(self, canvas: skia.Canvas, paint: skia.Paint = None):
        """Draw the image on the canvas."""
        if self.image is None:
            # Draw a placeholder rectangle if image failed to load
            self._draw_placeholder(canvas, paint)
        else:
            # Draw the image
            try:
                if paint is None:
                    paint = skia.Paint()
                    paint.setAntiAlias(True)

                # Calculate scale factor
                scale_x = self.width / self.image.width()
                scale_y = self.height / self.image.height()

                # Use canvas transform for scaling
                canvas.save()
                canvas.translate(self.x, self.y)
                canvas.scale(scale_x, scale_y)
                # drawImage signature: (image, left, top, sampling_options, paint)
                sampling = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
                canvas.drawImage(self.image, 0, 0, sampling, paint)
                canvas.restore()
            except Exception as e:
                logger.error(f"Failed to draw image: {e}")
                # If drawing fails, fall back to placeholder
                self._draw_placeholder(canvas, paint)

    def _draw_placeholder(self, canvas: skia.Canvas, paint: skia.Paint = None):
        """Draw a placeholder for a missing or failed image."""
        if paint is None:
            paint = skia.Paint()
            paint.setColor(skia.ColorLTGRAY)
            paint.setStyle(skia.Paint.kFill_Style)
        rect = skia.Rect.MakeLTRB(self.x, self.y, self.x + self.width, self.y + self.height)
        canvas.drawRect(rect, paint)

        # Draw border
        border_paint = skia.Paint()
        border_paint.setColor(skia.ColorGRAY)
        border_paint.setStyle(skia.Paint.kStroke_Style)
        border_paint.setStrokeWidth(1)
        canvas.drawRect(rect, border_paint)

        # Draw alt text if available
        if self.alt_text:
            text_paint = skia.Paint()
            text_paint.setAntiAlias(True)
            text_paint.setColor(skia.ColorBLACK)
            font = get_font(12)
            canvas.drawString(self.alt_text, self.x + 5, self.y + 15, font, text_paint)



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
