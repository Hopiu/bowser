"""CSS parser with tokenizer, selector parsing, and property declarations.

Supports:
- Tag selectors (p, div, h1)
- Class selectors (.classname)
- ID selectors (#idname)
- Property declarations (color: red; font-size: 14px;)
- Inline styles (style attribute)
"""

import re
from typing import List, Dict, Tuple


class Selector:
    """CSS selector with specificity calculation."""

    def __init__(self, text: str):
        self.text = text.strip()
        self.tag = None
        self.id = None
        self.classes = []
        self._parse()

    def _parse(self):
        """Parse selector into tag, id, and classes."""
        remaining = self.text

        # Parse ID (#id)
        if "#" in remaining:
            id_match = re.search(r'#([\w-]+)', remaining)
            if id_match:
                self.id = id_match.group(1)
                remaining = remaining.replace(f"#{self.id}", "")

        # Parse classes (.class)
        class_matches = re.findall(r'\.([\w-]+)', remaining)
        self.classes = class_matches
        for cls in class_matches:
            remaining = remaining.replace(f".{cls}", "", 1)

        # What's left is the tag
        remaining = remaining.strip()
        if remaining and remaining.isalnum():
            self.tag = remaining

    def specificity(self) -> Tuple[int, int, int]:
        """
        Calculate specificity as (id_count, class_count, tag_count).
        Higher specificity wins in cascade.
        """
        id_count = 1 if self.id else 0
        class_count = len(self.classes)
        tag_count = 1 if self.tag else 0
        return (id_count, class_count, tag_count)

    def matches(self, element) -> bool:
        """Check if this selector matches the given element."""
        # Check tag
        if self.tag and element.tag != self.tag:
            return False

        # Check ID
        if self.id:
            elem_id = element.attributes.get("id", "")
            if elem_id != self.id:
                return False

        # Check classes
        if self.classes:
            elem_classes = element.attributes.get("class", "").split()
            for cls in self.classes:
                if cls not in elem_classes:
                    return False

        return True

    def __repr__(self):
        return f"Selector({self.text!r})"


class CSSRule:
    """A CSS rule with selector and property declarations."""

    def __init__(self, selector: Selector, declarations: Dict[str, str]):
        self.selector = selector
        self.declarations = declarations

    def __repr__(self):
        return f"CSSRule({self.selector.text!r}, {self.declarations!r})"


class CSSParser:
    """Parser for CSS stylesheets."""

    def __init__(self, css_text: str):
        self.css_text = css_text
        self.position = 0
        self.rules = []

    def parse(self) -> List[CSSRule]:
        """Parse CSS text into a list of rules."""
        self.rules = []
        self.position = 0

        while self.position < len(self.css_text):
            self._skip_whitespace()
            if self.position >= len(self.css_text):
                break

            # Skip comments
            if self._peek(2) == "/*":
                self._skip_comment()
                continue

            # Parse rule(s) - may return multiple rules for multi-selectors
            rules = self._parse_rule()
            if rules:
                if isinstance(rules, list):
                    self.rules.extend(rules)
                else:
                    self.rules.append(rules)

        return self.rules

    def _peek(self, count=1) -> str:
        """Peek ahead without consuming."""
        return self.css_text[self.position:self.position + count]

    def _consume(self, count=1) -> str:
        """Consume and return characters."""
        result = self.css_text[self.position:self.position + count]
        self.position += count
        return result

    def _skip_whitespace(self):
        """Skip whitespace and newlines."""
        while self.position < len(self.css_text) and self.css_text[self.position] in " \t\n\r":
            self.position += 1

    def _skip_comment(self):
        """Skip CSS comment /* ... */."""
        if self._peek(2) == "/*":
            self._consume(2)
            while self.position < len(self.css_text) - 1:
                if self._peek(2) == "*/":
                    self._consume(2)
                    break
                self._consume()

    def _parse_rule(self):
        """
        Parse a single CSS rule: selector { declarations }.
        Returns a CSSRule, or a list of CSSRules if the selector contains commas (multi-selector).
        """
        # Parse selector
        selector_text = ""
        while self.position < len(self.css_text):
            char = self._peek()
            if char == "{":
                break
            selector_text += self._consume()

        if not selector_text.strip():
            return None

        # Expect {
        self._skip_whitespace()
        if self._peek() != "{":
            return None
        self._consume()  # consume {

        # Parse declarations
        declarations = self._parse_declarations()

        # Expect }
        self._skip_whitespace()
        if self._peek() == "}":
            self._consume()

        # Split multi-selectors by comma
        selector_parts = [s.strip() for s in selector_text.split(',') if s.strip()]

        if len(selector_parts) == 1:
            # Single selector
            return CSSRule(Selector(selector_text), declarations)
        else:
            # Multi-selector: create one rule per selector with the same declarations
            return [CSSRule(Selector(part), declarations) for part in selector_parts]

    def _parse_declarations(self) -> Dict[str, str]:
        """Parse property declarations inside { }."""
        declarations = {}

        while self.position < len(self.css_text):
            self._skip_whitespace()

            # Check for end of block
            if self._peek() == "}":
                break

            # Parse property name
            prop_name = ""
            while self.position < len(self.css_text):
                char = self._peek()
                if char in ":}":
                    break
                prop_name += self._consume()

            prop_name = prop_name.strip()
            if not prop_name:
                break

            # Expect :
            self._skip_whitespace()
            if self._peek() != ":":
                break
            self._consume()  # consume :

            # Parse property value
            self._skip_whitespace()
            prop_value = ""
            while self.position < len(self.css_text):
                char = self._peek()
                if char in ";}":
                    break
                prop_value += self._consume()

            prop_value = prop_value.strip()

            # Store property
            if prop_name and prop_value:
                declarations[prop_name] = prop_value

            # Consume optional ;
            self._skip_whitespace()
            if self._peek() == ";":
                self._consume()

        return declarations


def parse_inline_style(style_attr: str) -> Dict[str, str]:
    """
    Parse inline style attribute into property declarations.

    Example: "color: red; font-size: 14px" -> {"color": "red", "font-size": "14px"}
    """
    declarations = {}

    # Split by semicolons
    parts = style_attr.split(";")
    for part in parts:
        part = part.strip()
        if not part or ":" not in part:
            continue

        prop, value = part.split(":", 1)
        prop = prop.strip()
        value = value.strip()

        if prop and value:
            declarations[prop] = value

    return declarations


def parse(css_text: str) -> List[CSSRule]:
    """Parse CSS text into a list of rules."""
    parser = CSSParser(css_text)
    return parser.parse()
