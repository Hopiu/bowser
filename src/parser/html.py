"""HTML parser stubs."""

import re


class Text:
    def __init__(self, text, parent=None):
        self.text = text
        self.parent = parent

    def __repr__(self):  # pragma: no cover - debug helper
        return f"Text({self.text!r})"


class Element:
    def __init__(self, tag, attributes=None, parent=None):
        self.tag = tag
        self.attributes = attributes or {}
        self.children = []
        self.parent = parent

    def __repr__(self):  # pragma: no cover - debug helper
        return f"Element({self.tag!r}, {self.attributes!r})"


def print_tree(node, indent=0):
    spacer = "  " * indent
    print(f"{spacer}{node}")
    if hasattr(node, "children"):
        for child in node.children:
            print_tree(child, indent + 1)


def parse_html(html_text: str) -> Element:
    """
    Very basic HTML parser that extracts text content.
    For now, just removes tags and returns a simple tree.
    """
    # Strip HTML tags for basic text extraction
    text_content = re.sub(r'<script[^>]*>.*?</script>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
    text_content = re.sub(r'<style[^>]*>.*?</style>', '', text_content, flags=re.DOTALL | re.IGNORECASE)
    text_content = re.sub(r'<[^>]+>', ' ', text_content)
    
    # Decode HTML entities
    text_content = text_content.replace('&lt;', '<')
    text_content = text_content.replace('&gt;', '>')
    text_content = text_content.replace('&amp;', '&')
    text_content = text_content.replace('&quot;', '"')
    text_content = text_content.replace('&#39;', "'")
    text_content = text_content.replace('&nbsp;', ' ')
    
    # Clean up whitespace
    text_content = re.sub(r'\s+', ' ', text_content).strip()
    
    # Create a simple document structure
    root = Element("html")
    body = Element("body", parent=root)
    root.children.append(body)
    
    if text_content:
        text_node = Text(text_content, parent=body)
        body.children.append(text_node)
    
    return root
