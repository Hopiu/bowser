"""Document-level layout."""

from ..parser.html import Element, Text
from ..render.fonts import get_font, linespace
from .embed import ImageLayout


class LayoutLine:
    """A laid-out line ready for rendering."""

    def __init__(self, text: str, x: float, y: float, font_size: int, char_positions: list = None, font_family: str = ""):
        self.text = text
        self.x = x
        self.y = y  # Top of line
        self.font_size = font_size
        self.font_family = font_family
        self.height = linespace(font_size)
        self.width = 0
        self.char_positions = char_positions or []

        # Calculate width - pass text to get_font for proper font selection
        if text:
            font = get_font(font_size, font_family, text=text)
            self.width = font.measureText(text)


class LayoutImage:
    """A laid-out image ready for rendering."""

    def __init__(self, image_layout: ImageLayout, x: float, y: float):
        self.image_layout = image_layout
        self.x = x
        self.y = y
        # Store initial dimensions but also provide dynamic access
        self._initial_width = image_layout.width
        self._initial_height = image_layout.height
    
    @property
    def width(self) -> float:
        """Get current width (may update after async image load)."""
        return self.image_layout.width if self.image_layout.width > 0 else self._initial_width
    
    @property
    def height(self) -> float:
        """Get current height (may update after async image load)."""
        return self.image_layout.height if self.image_layout.height > 0 else self._initial_height


class LayoutBlock:
    """A laid-out block with its lines."""

    def __init__(self, tag: str, block_type: str = "block"):
        self.tag = tag
        self.block_type = block_type
        self.lines = []  # List of LayoutLine
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0


class DocumentLayout:
    """Layout engine for a document."""

    def __init__(self, node, frame=None, base_url=None, async_images: bool = False):
        self.node = node
        self.frame = frame
        self.base_url = base_url  # For resolving relative image URLs
        self.async_images = async_images  # Load images in background
        self.blocks = []  # List of LayoutBlock
        self.lines = []   # Flat list of all LayoutLine for rendering
        self.images = []  # List of LayoutImage for rendering
        self.width = 0
        self.height = 0

    def layout(self, width: int, x_margin: int = 20, y_start: int = 30) -> list:
        """
        Layout the document and return a list of LayoutLine objects.

        Returns:
            List of LayoutLine objects ready for rendering
        """
        self.width = width
        max_width = max(10, width - 2 * x_margin)
        y = y_start

        self.blocks = []
        self.lines = []
        self.images = []

        # Find body
        body = self._find_body(self.node)
        if not body:
            return self.lines

        # Collect and layout blocks
        raw_blocks = self._collect_blocks(body)

        for block_info in raw_blocks:
            # Handle images separately
            if block_info.get("is_image"):
                image_layout = block_info.get("image_layout")
                if image_layout:
                    margin_top = block_info.get("margin_top", 6)
                    margin_bottom = block_info.get("margin_bottom", 10)
                    y += margin_top
                    
                    # Position the image
                    image_layout.x = x_margin
                    image_layout.y = y
                    
                    # Add to images list for rendering
                    layout_image = LayoutImage(image_layout, x_margin, y)
                    self.images.append(layout_image)
                    
                    y += image_layout.height + margin_bottom
                continue
            
            font_size = block_info.get("font_size", 14)
            font_family = block_info.get("font_family", "")
            text = block_info.get("text", "")
            margin_top = block_info.get("margin_top", 6)
            margin_bottom = block_info.get("margin_bottom", 10)
            block_type = block_info.get("block_type", "block")
            tag = block_info.get("tag", "")

            if not text:
                y += font_size * 0.6
                continue

            # Optional bullet prefix
            if block_info.get("bullet"):
                text = f"• {text}"

            layout_block = LayoutBlock(tag, block_type)
            layout_block.x = x_margin
            layout_block.y = y + margin_top

            # Word wrap - pass text to get appropriate font
            font = get_font(font_size, font_family, text=text)
            words = text.split()
            wrapped_lines = []
            current_line = []
            current_width = 0

            for word in words:
                word_width = font.measureText(word + " ")
                if current_width + word_width > max_width and current_line:
                    wrapped_lines.append(" ".join(current_line))
                    current_line = [word]
                    current_width = word_width
                else:
                    current_line.append(word)
                    current_width += word_width
            if current_line:
                wrapped_lines.append(" ".join(current_line))

            # Create LayoutLines
            line_height = linespace(font_size)
            y += margin_top
            block_start_y = y

            for line_text in wrapped_lines:
                # Calculate character positions
                char_positions = [0.0]
                for i in range(1, len(line_text) + 1):
                    char_positions.append(font.measureText(line_text[:i]))

                layout_line = LayoutLine(
                    text=line_text,
                    x=x_margin,
                    y=y,  # Top of line, baseline is y + font_size
                    font_size=font_size,
                    char_positions=char_positions,
                    font_family=font_family
                )

                layout_block.lines.append(layout_line)
                self.lines.append(layout_line)
                y += line_height

            layout_block.height = y - block_start_y
            layout_block.width = max_width
            self.blocks.append(layout_block)

            y += margin_bottom

        self.height = y + 50  # Padding at bottom
        return self.lines

    def _find_body(self, node):
        """Find the body element in the document."""
        if isinstance(node, Element) and node.tag == "body":
            return node
        if hasattr(node, "children"):
            for child in node.children:
                if isinstance(child, Element) and child.tag == "body":
                    return child
                found = self._find_body(child)
                if found:
                    return found
        return None

    def _collect_blocks(self, node) -> list:
        """Collect renderable blocks from the DOM."""
        blocks = []

        for child in getattr(node, "children", []):
            if isinstance(child, Text):
                txt = child.text.strip()
                if txt:
                    # Use computed style if available
                    style = getattr(child, "computed_style", None)
                    font_size = style.get_int("font-size", 14) if style else 14
                    font_family = style.get("font-family", "") if style else ""
                    blocks.append({
                        "text": txt,
                        "font_size": font_size,
                        "font_family": font_family,
                        "block_type": "text",
                        "style": style
                    })
                continue

            if isinstance(child, Element):
                tag = child.tag.lower()

                # Skip style and script tags - they shouldn't be rendered
                if tag in {"style", "script", "head", "title", "meta", "link"}:
                    continue
                
                # Handle img tags
                if tag == "img":
                    image_layout = ImageLayout(child)
                    image_layout.load(self.base_url, async_load=self.async_images)
                    image_layout.layout(max_width=self.width - 40 if self.width > 40 else 800)
                    
                    # Get computed style for margins
                    style = getattr(child, "computed_style", None)
                    if style:
                        margin_top = style.get_int("margin-top", 6)
                        margin_bottom = style.get_int("margin-bottom", 10)
                    else:
                        margin_top = 6
                        margin_bottom = 10
                    
                    blocks.append({
                        "is_image": True,
                        "image_layout": image_layout,
                        "margin_top": margin_top,
                        "margin_bottom": margin_bottom,
                    })
                    continue

                # Container elements - just recurse, don't add as blocks
                if tag in {"ul", "ol", "div", "section", "article", "main", "header", "footer", "nav"}:
                    blocks.extend(self._collect_blocks(child))
                    continue

                # For other elements (p, h1, etc), first collect any embedded images
                embedded_images = self._collect_images(child)
                blocks.extend(embedded_images)
                
                content = self._text_of(child)
                if not content:
                    continue

                # Get computed style for this element
                style = getattr(child, "computed_style", None)

                # Extract style properties
                if style:
                    font_size = style.get_int("font-size", 14)
                    margin_top = style.get_int("margin-top", 6)
                    margin_bottom = style.get_int("margin-bottom", 10)
                    display = style.get("display", "block")
                    font_family = style.get("font-family", "")
                else:
                    # Fallback to hardcoded defaults
                    font_size = self._get_default_font_size(tag)
                    margin_top = self._get_default_margin_top(tag)
                    margin_bottom = self._get_default_margin_bottom(tag)
                    display = "inline" if tag in {"span", "a", "strong", "em", "b", "i", "code"} else "block"
                    font_family = ""

                # Determine block type
                block_type = "inline" if display == "inline" else "block"
                if tag == "li" or display == "list-item":
                    block_type = "list-item"

                # Add bullet for list items
                bullet = (tag == "li" or display == "list-item")

                blocks.append({
                    "text": content,
                    "font_size": font_size,
                    "font_family": font_family,
                    "margin_top": margin_top,
                    "margin_bottom": margin_bottom,
                    "block_type": block_type,
                    "tag": tag,
                    "bullet": bullet,
                    "style": style
                })

        return blocks

    def _get_default_font_size(self, tag: str) -> int:
        """Get default font size for a tag (fallback when no styles)."""
        sizes = {
            "h1": 24, "h2": 20, "h3": 18, "h4": 16, "h5": 15, "h6": 14
        }
        return sizes.get(tag, 14)

    def _get_default_margin_top(self, tag: str) -> int:
        """Get default top margin for a tag (fallback when no styles)."""
        margins = {
            "h1": 12, "h2": 10, "h3": 8, "p": 6, "li": 4
        }
        return margins.get(tag, 0)

    def _get_default_margin_bottom(self, tag: str) -> int:
        """Get default bottom margin for a tag (fallback when no styles)."""
        margins = {
            "h1": 12, "h2": 10, "h3": 8, "p": 12, "li": 4
        }
        return margins.get(tag, 0)

    def _collect_images(self, node) -> list:
        """Recursively collect all img elements from a node."""
        images = []
        
        if not isinstance(node, Element):
            return images
        
        for child in getattr(node, "children", []):
            if isinstance(child, Element):
                if child.tag.lower() == "img":
                    image_layout = ImageLayout(child)
                    image_layout.load(self.base_url, async_load=self.async_images)
                    image_layout.layout(max_width=self.width - 40 if self.width > 40 else 800)
                    
                    style = getattr(child, "computed_style", None)
                    if style:
                        margin_top = style.get_int("margin-top", 6)
                        margin_bottom = style.get_int("margin-bottom", 10)
                    else:
                        margin_top = 6
                        margin_bottom = 10
                    
                    images.append({
                        "is_image": True,
                        "image_layout": image_layout,
                        "margin_top": margin_top,
                        "margin_bottom": margin_bottom,
                    })
                else:
                    # Recurse into children
                    images.extend(self._collect_images(child))
        
        return images
    
    def _text_of(self, node) -> str:
        """Extract text content from a node."""
        if isinstance(node, Text):
            return node.text
        if isinstance(node, Element):
            parts = []
            for child in node.children:
                parts.append(self._text_of(child))
            return " ".join([p for p in parts if p]).strip()
        return ""
