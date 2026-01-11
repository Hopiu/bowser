"""Very small HTML parser that builds a simple DOM tree."""

from html import unescape
from html.parser import HTMLParser
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


class _DOMBuilder(HTMLParser):
    """Tiny HTML parser that produces Element/Text nodes."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.root = Element("html")
        self.current = self.root
        self._skip_depth = 0  # for script/style skipping
        self._body = None  # The body element (real or implicit)

    def _ensure_body(self):
        """Ensure we have a body element to add content to."""
        if self._body is None:
            self._body = Element("body", parent=self.root)
            self.root.children.append(self._body)
        if self.current is self.root:
            self.current = self._body

    # Helpers
    def _push(self, el: Element):
        el.parent = self.current
        self.current.children.append(el)
        self.current = el

    def _pop(self, tag: str):
        node = self.current
        while node and node is not self.root:
            if getattr(node, "tag", None) == tag:
                self.current = node.parent or self._body or self.root
                return
            node = node.parent
        self.current = self._body or self.root

    def _append_text(self, text: str):
        """Append text to current node, merging with previous text when possible."""
        if not text:
            return
        last = self.current.children[-1] if self.current.children else None
        if isinstance(last, Text):
            # Avoid accumulating duplicate whitespace when merging segments
            if last.text.endswith(" ") and text.startswith(" "):
                text = text.lstrip()
            last.text += text
        else:
            self.current.children.append(Text(text, parent=self.current))

    # HTMLParser callbacks
    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self._skip_depth += 1
            return
        if self._skip_depth > 0:
            return
        
        # Skip html/head tags - we handle structure ourselves
        if tag == "html":
            return  # Use our root instead
        if tag == "head":
            self._skip_depth += 1  # Skip head content
            return
        if tag == "body":
            if self._body is None:
                # Create the body element
                attr_dict = {k: v for k, v in attrs}
                self._body = Element("body", attr_dict, parent=self.root)
                self.root.children.append(self._body)
            self.current = self._body
            return
            
        attr_dict = {k: v for k, v in attrs}
        el = Element(tag, attr_dict)
        
        # Ensure we're inside a body
        if self.current is self.root:
            self._ensure_body()
        
        self._push(el)

    def handle_endtag(self, tag):
        if tag in {"script", "style", "head"}:
            if self._skip_depth > 0:
                self._skip_depth -= 1
            return
        if self._skip_depth > 0:
            return
        if tag in {"html", "body"}:
            return  # Don't pop these
        self._pop(tag)

    def handle_data(self, data):
        if self._skip_depth > 0:
            return
        text = unescape(data)
        # Collapse whitespace
        if not text:
            return
        text = re.sub(r"\s+", " ", text)
        if not text.strip():
            return  # Skip whitespace-only text at root level
        
        # Ensure we're inside a body for text content
        if self.current is self.root:
            self._ensure_body()
        
        self._append_text(text)

    def handle_entityref(self, name):
        self.handle_data(f"&{name};")

    def handle_charref(self, name):
        self.handle_data(f"&#{name};")


def parse_html(html_text: str) -> Element:
    """
    Parse HTML into a small DOM tree of Element/Text nodes.
    - Scripts and styles are skipped
    - Whitespace is normalized within text nodes
    - Entities are decoded
    - A root <html><body> is always provided
    """
    parser = _DOMBuilder()
    parser.feed(html_text)
    parser.close()
    return parser.root
