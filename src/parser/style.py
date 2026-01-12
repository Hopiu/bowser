"""Style computation and cascade resolution.

This module handles:
- Computing final styles for each element
- Cascade: inline > id > class > tag
- Inheritance: font properties inherit from parent
- Default styles for each element type
"""

from typing import Dict, List, Optional
from .css import CSSRule, parse_inline_style


# Default styles for different element types
DEFAULT_STYLES = {
    # Block-level elements
    "body": {"display": "block", "margin": "8px"},
    "div": {"display": "block"},
    "p": {"display": "block", "margin-top": "16px", "margin-bottom": "16px"},
    "h1": {
        "display": "block", "font-size": "32px", "font-weight": "bold",
        "margin-top": "20px", "margin-bottom": "20px"
    },
    "h2": {
        "display": "block", "font-size": "24px", "font-weight": "bold",
        "margin-top": "18px", "margin-bottom": "18px"
    },
    "h3": {
        "display": "block", "font-size": "20px", "font-weight": "bold",
        "margin-top": "16px", "margin-bottom": "16px"
    },
    "h4": {
        "display": "block", "font-size": "18px", "font-weight": "bold",
        "margin-top": "14px", "margin-bottom": "14px"
    },
    "h5": {
        "display": "block", "font-size": "16px", "font-weight": "bold",
        "margin-top": "12px", "margin-bottom": "12px"
    },
    "h6": {
        "display": "block", "font-size": "14px", "font-weight": "bold",
        "margin-top": "10px", "margin-bottom": "10px"
    },
    "ul": {
        "display": "block", "margin-top": "16px", "margin-bottom": "16px",
        "padding-left": "40px"
    },
    "ol": {
        "display": "block", "margin-top": "16px", "margin-bottom": "16px",
        "padding-left": "40px"
    },
    "li": {"display": "list-item"},
    "blockquote": {
        "display": "block", "margin-top": "16px", "margin-bottom": "16px",
        "margin-left": "40px", "margin-right": "40px"
    },
    "pre": {
        "display": "block", "font-family": "monospace",
        "margin-top": "16px", "margin-bottom": "16px"
    },

    # Inline elements
    "span": {"display": "inline"},
    "a": {"display": "inline", "color": "blue", "text-decoration": "underline"},
    "em": {"display": "inline", "font-style": "italic"},
    "i": {"display": "inline", "font-style": "italic"},
    "strong": {"display": "inline", "font-weight": "bold"},
    "b": {"display": "inline", "font-weight": "bold"},
    "code": {"display": "inline", "font-family": "monospace"},
}

# Properties that inherit from parent
INHERITED_PROPERTIES = {
    "color",
    "font-family",
    "font-size",
    "font-style",
    "font-weight",
    "line-height",
    "text-align",
    "text-decoration",
}


class ComputedStyle:
    """Computed style for an element."""

    def __init__(self, properties: Optional[Dict[str, str]] = None):
        self.properties = properties or {}

    def get(self, name: str, default: str = "") -> str:
        """Get a style property value."""
        return self.properties.get(name, default)

    def set(self, name: str, value: str):
        """Set a style property value."""
        self.properties[name] = value

    def get_int(self, name: str, default: int = 0) -> int:
        """Get a style property as an integer (parsing px values)."""
        value = self.get(name)
        if not value:
            return default

        # Remove 'px' suffix if present
        if value.endswith("px"):
            value = value[:-2]

        try:
            return int(value)
        except ValueError:
            return default

    def get_float(self, name: str, default: float = 0.0) -> float:
        """Get a style property as a float (parsing px values)."""
        value = self.get(name)
        if not value:
            return default

        # Remove 'px' suffix if present
        if value.endswith("px"):
            value = value[:-2]

        try:
            return float(value)
        except ValueError:
            return default

    def __repr__(self):
        return f"ComputedStyle({self.properties!r})"


class StyleResolver:
    """Resolves styles for elements using cascade and inheritance."""

    def __init__(self, stylesheet_rules: Optional[List[CSSRule]] = None):
        self.stylesheet_rules = stylesheet_rules or []

    def resolve_style(self, element, parent_style: Optional[ComputedStyle] = None) -> ComputedStyle:
        """
        Compute the final style for an element.

        Cascade order (later wins):
        1. Default browser styles
        2. Inherited properties from parent
        3. Stylesheet rules (by specificity)
        4. Inline styles
        """
        style = ComputedStyle()

        # 1. Apply default styles
        tag = getattr(element, "tag", "")
        if tag in DEFAULT_STYLES:
            for prop, value in DEFAULT_STYLES[tag].items():
                style.set(prop, value)

        # 2. Inherit from parent
        if parent_style:
            for prop in INHERITED_PROPERTIES:
                value = parent_style.get(prop)
                if value:
                    style.set(prop, value)

        # 3. Apply stylesheet rules (sorted by specificity)
        matching_rules = []
        for rule in self.stylesheet_rules:
            if rule.selector.matches(element):
                matching_rules.append(rule)

        # Sort by specificity (lowest to highest)
        matching_rules.sort(key=lambda r: r.selector.specificity())

        for rule in matching_rules:
            for prop, value in rule.declarations.items():
                style.set(prop, value)

        # 4. Apply inline styles (highest priority)
        inline_style = element.attributes.get("style", "")
        if inline_style:
            inline_decls = parse_inline_style(inline_style)
            for prop, value in inline_decls.items():
                style.set(prop, value)

        return style

    def resolve_tree(self, root, parent_style: Optional[ComputedStyle] = None):
        """
        Recursively resolve styles for an entire DOM tree.
        Attaches computed_style attribute to each element.
        """
        # Resolve style for this element
        if hasattr(root, "tag"):  # Element node
            root.computed_style = self.resolve_style(root, parent_style)
            current_style = root.computed_style
        else:  # Text node
            root.computed_style = parent_style
            current_style = parent_style

        # Recursively resolve children
        if hasattr(root, "children"):
            for child in root.children:
                self.resolve_tree(child, current_style)
