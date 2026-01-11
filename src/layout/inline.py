"""Inline and text layout."""

from ..render.fonts import get_font, measure_text, linespace


class TextLayout:
    """Layout for a single word/text run."""
    
    def __init__(self, node, word: str, parent=None, previous=None):
        self.node = node
        self.word = word
        self.parent = parent
        self.previous = previous
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.font_size = 14
    
    def layout(self, font_size: int = 14):
        """Calculate layout for this text."""
        self.font_size = font_size
        font = get_font(font_size)
        self.width = font.measureText(self.word)
        self.height = linespace(font_size)
        return self.width


class InlineLayout:
    """Layout for inline content (text runs within a line)."""
    
    def __init__(self, node, parent=None):
        self.node = node
        self.parent = parent
        self.children = []
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
    
    def add_word(self, word: str, font_size: int = 14):
        """Add a word to this inline layout."""
        text_layout = TextLayout(self.node, word, parent=self)
        text_layout.layout(font_size)
        self.children.append(text_layout)
        return text_layout
    
    def layout(self, x: float, y: float, max_width: float, font_size: int = 14):
        """Layout all words, wrapping as needed. Returns list of lines."""
        lines = []
        current_line = []
        current_x = x
        line_y = y
        line_height = linespace(font_size)
        
        for child in self.children:
            if current_x + child.width > x + max_width and current_line:
                # Wrap to next line
                lines.append((current_line, line_y, line_height))
                current_line = []
                current_x = x
                line_y += line_height
            
            child.x = current_x
            child.y = line_y
            current_line.append(child)
            current_x += child.width
        
        if current_line:
            lines.append((current_line, line_y, line_height))
        
        self.height = line_y + line_height - y if lines else 0
        return lines
