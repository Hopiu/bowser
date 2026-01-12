"""Render pipeline - coordinates layout and painting."""

import skia
from typing import Optional
from ..parser.html import Element
from ..layout.document import DocumentLayout
from .fonts import get_font
from .paint import DisplayList


class RenderPipeline:
    """Coordinates layout calculation and rendering to a Skia canvas."""

    def __init__(self):
        # Layout cache
        self._layout: Optional[DocumentLayout] = None
        self._layout_width = 0
        self._layout_doc_id = None

        # Paint cache
        self._text_paint: Optional[skia.Paint] = None
        self._display_list: Optional[DisplayList] = None

        # Debug mode
        self.debug_mode = False

    def layout(self, document: Element, width: int) -> DocumentLayout:
        """
        Calculate layout for the document.
        Returns the DocumentLayout with all positioned elements.
        """
        doc_id = id(document)

        # Check cache
        if (self._layout_doc_id == doc_id and
            self._layout_width == width and
            self._layout is not None):
            return self._layout

        # Build new layout
        self._layout = DocumentLayout(document)
        self._layout.layout(width)
        self._layout_doc_id = doc_id
        self._layout_width = width

        return self._layout

    def render(self, canvas: skia.Canvas, document: Element,
               width: int, height: int, scroll_y: float = 0):
        """
        Render the document to the canvas.

        Args:
            canvas: Skia canvas to draw on
            document: DOM document root
            width: Viewport width
            height: Viewport height
            scroll_y: Vertical scroll offset
        """
        # Get or update layout
        layout = self.layout(document, width)

        if not layout.lines:
            return

        # Apply scroll transform
        canvas.save()
        canvas.translate(0, -scroll_y)

        # Get paint
        if self._text_paint is None:
            self._text_paint = skia.Paint()
            self._text_paint.setAntiAlias(True)
            self._text_paint.setColor(skia.ColorBLACK)

        # Render visible lines only
        visible_top = scroll_y - 50
        visible_bottom = scroll_y + height + 50

        for line in layout.lines:
            baseline_y = line.y + line.font_size
            if baseline_y < visible_top or line.y > visible_bottom:
                continue

            font = get_font(line.font_size)
            canvas.drawString(line.text, line.x, baseline_y, font, self._text_paint)

        # Draw debug overlays if enabled
        if self.debug_mode:
            self._render_debug_overlays(canvas, layout)

        canvas.restore()

    def _render_debug_overlays(self, canvas: skia.Canvas, layout: DocumentLayout):
        """Render debug bounding boxes for layout blocks."""
        # Color scheme for different block types
        colors = {
            "block": (255, 0, 0, 60),      # Red
            "inline": (0, 0, 255, 60),     # Blue
            "list-item": (0, 255, 0, 60),  # Green
            "text": (255, 255, 0, 60),     # Yellow
        }

        border_colors = {
            "block": (255, 0, 0, 180),
            "inline": (0, 0, 255, 180),
            "list-item": (0, 255, 0, 180),
            "text": (255, 255, 0, 180),
        }

        for block in layout.blocks:
            block_type = block.block_type

            # Calculate block bounds from lines
            if not block.lines:
                continue

            x = block.x - 5
            y = block.y - block.lines[0].font_size if block.lines else block.y
            w = block.width + 10
            h = block.height + 5

            # Fill
            fill_paint = skia.Paint()
            c = colors.get(block_type, colors["block"])
            fill_paint.setColor(skia.Color(*c))
            fill_paint.setStyle(skia.Paint.kFill_Style)

            rect = skia.Rect.MakeLTRB(x, y, x + w, y + h)
            canvas.drawRect(rect, fill_paint)

            # Border
            border_paint = skia.Paint()
            bc = border_colors.get(block_type, border_colors["block"])
            border_paint.setColor(skia.Color(*bc))
            border_paint.setStyle(skia.Paint.kStroke_Style)
            border_paint.setStrokeWidth(1)
            canvas.drawRect(rect, border_paint)

    def get_text_layout(self) -> list:
        """
        Get the text layout for text selection.
        Returns list of line info dicts with char_positions.
        """
        if self._layout is None:
            return []

        result = []
        for line in self._layout.lines:
            result.append({
                "text": line.text,
                "x": line.x,
                "y": line.y,
                "width": line.width,
                "height": line.height,
                "font_size": line.font_size,
                "char_positions": line.char_positions
            })
        return result

    def get_document_height(self) -> float:
        """Get the total document height for scrolling."""
        if self._layout is None:
            return 0
        return self._layout.height

    def invalidate(self):
        """Invalidate the layout cache, forcing recalculation."""
        self._layout = None
        self._layout_doc_id = None
        self._display_list = None
