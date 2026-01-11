"""Block and line layout."""

from ..render.fonts import get_font, linespace
from ..parser.html import Element, Text


class LineLayout:
    """Layout for a single line of text."""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.words = []  # List of (text, x, font_size)
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.font_size = 14
    
    def add_word(self, word: str, x: float, font_size: int):
        """Add a word to this line."""
        self.words.append((word, x, font_size))
        font = get_font(font_size)
        word_width = font.measureText(word + " ")
        self.width = max(self.width, x + word_width - self.x)
        self.height = max(self.height, linespace(font_size))


class BlockLayout:
    """Layout for a block-level element."""
    
    def __init__(self, node, parent=None, previous=None, frame=None):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.frame = frame
        self.children = []  # Child BlockLayouts
        self.lines = []     # LineLayouts for inline content
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.margin_top = 0
        self.margin_bottom = 0
        self.font_size = 14
        self.block_type = "block"
        self.tag = ""
    
    def layout(self, x: float, y: float, max_width: float):
        """Layout this block and return the height used."""
        self.x = x
        self.y = y
        self.width = max_width
        
        current_y = y + self.margin_top
        
        # Layout children
        for child in self.children:
            child.layout(x, current_y, max_width)
            current_y += child.height + child.margin_bottom
        
        # Layout lines
        for line in self.lines:
            line.y = current_y
            current_y += line.height
        
        self.height = current_y - y + self.margin_bottom
        return self.height


def build_block_layout(node, parent=None, font_size: int = 14, 
                       margin_top: int = 6, margin_bottom: int = 10,
                       block_type: str = "block", bullet: bool = False) -> BlockLayout:
    """Build a BlockLayout from a DOM node."""
    block = BlockLayout(node, parent)
    block.font_size = font_size
    block.margin_top = margin_top
    block.margin_bottom = margin_bottom
    block.block_type = block_type
    block.tag = node.tag if isinstance(node, Element) else ""
    
    # Collect text content
    text = _extract_text(node)
    if bullet and text:
        text = f"• {text}"
    
    if text:
        block._raw_text = text
    else:
        block._raw_text = ""
    
    return block


def _extract_text(node) -> str:
    """Extract text content from a node."""
    if isinstance(node, Text):
        return node.text
    if isinstance(node, Element):
        parts = []
        for child in node.children:
            parts.append(_extract_text(child))
        return " ".join([p for p in parts if p]).strip()
    return ""
