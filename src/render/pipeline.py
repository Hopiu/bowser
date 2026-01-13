"""Render pipeline - coordinates layout and painting."""

import skia
from typing import Optional, Callable
from ..parser.html import Element
from ..layout.document import DocumentLayout
from ..layout.embed import ImageLayout
from .fonts import get_font
from .paint import DisplayList, DrawImage


class RenderPipeline:
    """Coordinates layout calculation and rendering to a Skia canvas."""

    def __init__(self):
        # Layout cache
        self._layout: Optional[DocumentLayout] = None
        self._layout_width = 0
        self._layout_doc_id = None
        self._layout_base_url = None

        # Paint cache
        self._text_paint: Optional[skia.Paint] = None
        self._display_list: Optional[DisplayList] = None

        # Base URL for resolving relative paths
        self.base_url: Optional[str] = None

        # Debug mode
        self.debug_mode = False

        # Async image loading
        self.async_images = True  # Enable async image loading by default
        self._on_needs_redraw: Optional[Callable[[], None]] = None

    def set_redraw_callback(self, callback: Callable[[], None]):
        """Set a callback to be called when async images finish loading."""
        self._on_needs_redraw = callback

        # Also set on ImageLayout class for global notification
        def on_image_loaded():
            # Invalidate layout cache so positions are recalculated with actual image sizes
            self.invalidate()
            if self._on_needs_redraw:
                self._on_needs_redraw()

        ImageLayout._on_any_image_loaded = on_image_loaded

    def layout(self, document: Element, width: int) -> DocumentLayout:
        """
        Calculate layout for the document.
        Returns the DocumentLayout with all positioned elements.
        """
        doc_id = id(document)

        # Check cache (also invalidate if base_url changed)
        if (self._layout_doc_id == doc_id and
            self._layout_width == width and
            self._layout_base_url == self.base_url and
            self._layout is not None):
            return self._layout

        # Build new layout with base_url for resolving image paths
        self._layout = DocumentLayout(
            document,
            base_url=self.base_url,
            async_images=self.async_images
        )
        self._layout.layout(width)
        self._layout_doc_id = doc_id
        self._layout_width = width
        self._layout_base_url = self.base_url

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

        if not layout.lines and not layout.images:
            return

        # Apply scroll transform
        canvas.save()
        canvas.translate(0, -scroll_y)

        # Get paint
        if self._text_paint is None:
            self._text_paint = skia.Paint()
            self._text_paint.setAntiAlias(True)
            self._text_paint.setColor(skia.ColorBLACK)

        # Render visible content
        visible_top = scroll_y - 50
        visible_bottom = scroll_y + height + 50

        # Render visible lines
        for line in layout.lines:
            baseline_y = line.y + line.font_size
            if baseline_y < visible_top or line.y > visible_bottom:
                continue

            font = get_font(line.font_size, getattr(line, "font_family", ""), text=line.text)

            # Use line color if specified (for links), otherwise black
            paint = skia.Paint()
            paint.setAntiAlias(True)
            if line.color:
                paint.setColor(self._parse_color(line.color))
            else:
                paint.setColor(skia.ColorBLACK)

            canvas.drawString(line.text, line.x, baseline_y, font, paint)

            # Draw underline for links
            if line.href:
                underline_paint = skia.Paint()
                underline_paint.setColor(paint.getColor())
                underline_paint.setStyle(skia.Paint.kStroke_Style)
                underline_paint.setStrokeWidth(1)
                underline_y = baseline_y + 2
                canvas.drawLine(line.x, underline_y, line.x + line.width, underline_y, underline_paint)

        # Render visible images (both loaded and placeholder)
        for layout_image in layout.images:
            image_bottom = layout_image.y + layout_image.height
            if image_bottom < visible_top or layout_image.y > visible_bottom:
                continue

            image_layout = layout_image.image_layout
            # Use image_layout dimensions directly for accurate sizing after async load
            img_width = image_layout.width if image_layout.width > 0 else layout_image.width
            img_height = image_layout.height if image_layout.height > 0 else layout_image.height

            # Always create DrawImage command - it handles None images as placeholders
            draw_cmd = DrawImage(
                layout_image.x,
                layout_image.y,
                img_width,
                img_height,
                image_layout.image,  # May be None, DrawImage handles this
                image_layout.alt_text
            )
            draw_cmd.execute(canvas)

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
        Get the text layout for text selection and link hit testing.
        Returns list of line info dicts with char_positions and href.
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
                "char_positions": line.char_positions,
                "href": getattr(line, "href", None)
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

    def _parse_color(self, color_str: str) -> int:
        """Parse a CSS color string to a Skia color value.

        Supports:
        - Hex colors: #rgb, #rrggbb
        - Named colors (limited set)

        Note: Very light colors (like white) that would be invisible on
        our white background are converted to black.
        """
        if not color_str:
            return skia.ColorBLACK

        color_str = color_str.strip().lower()

        # Named colors
        named_colors = {
            "black": skia.ColorBLACK,
            "white": skia.ColorBLACK,  # White is invisible on white bg, use black
            "red": skia.ColorRED,
            "green": skia.ColorGREEN,
            "blue": skia.ColorBLUE,
            "yellow": skia.ColorYELLOW,
            "cyan": skia.ColorCYAN,
            "magenta": skia.ColorMAGENTA,
            "gray": skia.ColorGRAY,
            "grey": skia.ColorGRAY,
        }

        if color_str in named_colors:
            return named_colors[color_str]

        # Hex colors
        if color_str.startswith("#"):
            hex_str = color_str[1:]
            try:
                if len(hex_str) == 3:
                    # #rgb -> #rrggbb
                    r = int(hex_str[0] * 2, 16)
                    g = int(hex_str[1] * 2, 16)
                    b = int(hex_str[2] * 2, 16)
                elif len(hex_str) == 6:
                    r = int(hex_str[0:2], 16)
                    g = int(hex_str[2:4], 16)
                    b = int(hex_str[4:6], 16)
                else:
                    return skia.ColorBLACK

                # Check if color is too light (would be invisible on white)
                # Use relative luminance approximation
                if r > 240 and g > 240 and b > 240:
                    return skia.ColorBLACK

                return skia.Color(r, g, b, 255)
            except ValueError:
                pass

        # Fallback to black
        return skia.ColorBLACK
