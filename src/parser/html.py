"""Very small HTML parser that builds a simple DOM tree."""

from html import unescape
from html.parser import HTMLParser
import re


class Text:
    def __init__(self, text, parent=None):
        self.text = text
        self.parent = parent
        # Layout reference (set by layout engine)
        self.layout = None

    def __repr__(self):  # pragma: no cover - debug helper
        return f"Text({self.text!r})"


class Element:
    def __init__(self, tag, attributes=None, parent=None):
        self.tag = tag
        self.attributes = attributes or {}
        self.children = []
        self.parent = parent
        # Layout reference (set by layout engine)
        self.layout = None

    def __repr__(self):  # pragma: no cover - debug helper
        return f"Element({self.tag!r}, {self.attributes!r})"

    @property
    def bounding_box(self):
        """Get bounding box from layout if available."""
        if self.layout:
            return (self.layout.x, self.layout.y,
                    self.layout.x + self.layout.width,
                    self.layout.y + self.layout.height)
        return None


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
        if tag in {"script"}:
            self._skip_depth += 1
            return
        if self._skip_depth > 0:
            return

        # Skip html/head tags - we handle structure ourselves
        if tag == "html":
            return  # Use our root instead
        if tag == "head":
            # We skip head but need to preserve style tags
            return
        if tag == "body":
            if self._body is None:
                # Create the body element
                attr_dict = {k: v for k, v in attrs}
                self._body = Element("body", attr_dict, parent=self.root)
                self.root.children.append(self._body)
            self.current = self._body
            return

        # Handle style tags - keep them in the tree for CSS extraction
        if tag == "style":
            attr_dict = {k: v for k, v in attrs}
            el = Element(tag, attr_dict)
            self._push(el)
            return

        attr_dict = {k: v for k, v in attrs}
        el = Element(tag, attr_dict)

        # Ensure we're inside a body
        if self.current is self.root:
            self._ensure_body()

        self._push(el)

    def handle_endtag(self, tag):
        if tag in {"script"}:
            if self._skip_depth > 0:
                self._skip_depth -= 1
            return
        if self._skip_depth > 0:
            return
        if tag in {"html", "body", "head"}:
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


def parse_html_with_styles(html_text: str, apply_styles: bool = True) -> Element:
    """
    Parse HTML and optionally extract and apply CSS styles.

    Args:
        html_text: The HTML source code
        apply_styles: Whether to parse <style> tags and apply styles

    Returns:
        The root element with computed_style attributes on each node
    """
    from .css import parse as parse_css
    from .style import StyleResolver
    import os
    from pathlib import Path

    # Parse HTML
    root = parse_html(html_text)

    if not apply_styles:
        return root

    # Load default stylesheet
    css_rules = []
    default_css_path = Path(__file__).parent.parent.parent / "assets" / "default.css"
    if default_css_path.exists():
        with open(default_css_path, "r", encoding="utf-8") as f:
            default_css = f.read()
            default_rules = parse_css(default_css)
            css_rules.extend(default_rules)

    # Extract CSS from <style> tags
    style_elements = _find_elements_by_tag(root, "style")

    for style_elem in style_elements:
        # Extract text content from style element
        css_text = _text_of_element(style_elem)
        if css_text:
            rules = parse_css(css_text)
            css_rules.extend(rules)

    # Create style resolver and apply to tree
    resolver = StyleResolver(css_rules)
    resolver.resolve_tree(root)

    return root


def _find_elements_by_tag(node, tag: str) -> list:
    """Find all elements with a given tag name."""
    results = []
    if isinstance(node, Element) and node.tag == tag:
        results.append(node)
    if hasattr(node, "children"):
        for child in node.children:
            results.extend(_find_elements_by_tag(child, tag))
    return results


def _text_of_element(node) -> str:
    """Extract text content from an element."""
    if isinstance(node, Text):
        return node.text
    if isinstance(node, Element):
        parts = []
        for child in node.children:
            parts.append(_text_of_element(child))
        return " ".join([p for p in parts if p])
    return ""
