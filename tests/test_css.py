"""Tests for CSS parsing and style computation."""

import pytest
from src.parser.css import (
    Selector, CSSRule, CSSParser, parse, parse_inline_style
)
from src.parser.html import Element, Text
from src.parser.style import (
    ComputedStyle, StyleResolver, DEFAULT_STYLES, INHERITED_PROPERTIES
)


class TestSelector:
    """Test CSS selector parsing and matching."""
    
    def test_tag_selector(self):
        sel = Selector("p")
        assert sel.tag == "p"
        assert sel.id is None
        assert sel.classes == []
    
    def test_class_selector(self):
        sel = Selector(".container")
        assert sel.tag is None
        assert sel.classes == ["container"]
    
    def test_id_selector(self):
        sel = Selector("#header")
        assert sel.id == "header"
        assert sel.tag is None
    
    def test_compound_selector(self):
        sel = Selector("div.container")
        assert sel.tag == "div"
        assert sel.classes == ["container"]
    
    def test_complex_compound_selector(self):
        sel = Selector("div#main.container.active")
        assert sel.tag == "div"
        assert sel.id == "main"
        assert set(sel.classes) == {"container", "active"}
    
    def test_specificity_tag_only(self):
        sel = Selector("p")
        assert sel.specificity() == (0, 0, 1)
    
    def test_specificity_class_only(self):
        sel = Selector(".container")
        assert sel.specificity() == (0, 1, 0)
    
    def test_specificity_id_only(self):
        sel = Selector("#header")
        assert sel.specificity() == (1, 0, 0)
    
    def test_specificity_compound(self):
        sel = Selector("div#main.container.active")
        assert sel.specificity() == (1, 2, 1)
    
    def test_matches_tag(self):
        sel = Selector("p")
        elem = Element("p")
        assert sel.matches(elem) is True
        
        elem2 = Element("div")
        assert sel.matches(elem2) is False
    
    def test_matches_class(self):
        sel = Selector(".container")
        elem = Element("div", {"class": "container sidebar"})
        assert sel.matches(elem) is True
        
        elem2 = Element("div", {"class": "sidebar"})
        assert sel.matches(elem2) is False
    
    def test_matches_id(self):
        sel = Selector("#header")
        elem = Element("div", {"id": "header"})
        assert sel.matches(elem) is True
        
        elem2 = Element("div", {"id": "footer"})
        assert sel.matches(elem2) is False
    
    def test_matches_compound(self):
        sel = Selector("div.container")
        elem = Element("div", {"class": "container"})
        assert sel.matches(elem) is True
        
        # Wrong tag
        elem2 = Element("p", {"class": "container"})
        assert sel.matches(elem2) is False
        
        # Wrong class
        elem3 = Element("div", {"class": "sidebar"})
        assert sel.matches(elem3) is False


class TestCSSParser:
    """Test CSS stylesheet parsing."""
    
    def test_empty_stylesheet(self):
        rules = parse("")
        assert rules == []
    
    def test_single_rule(self):
        css = "p { color: red; }"
        rules = parse(css)
        assert len(rules) == 1
        assert rules[0].selector.tag == "p"
        assert rules[0].declarations == {"color": "red"}
    
    def test_multiple_rules(self):
        css = """
        p { color: red; }
        div { background: blue; }
        """
        rules = parse(css)
        assert len(rules) == 2
        assert rules[0].selector.tag == "p"
        assert rules[1].selector.tag == "div"
    
    def test_multiple_declarations(self):
        css = "p { color: red; font-size: 14px; margin: 10px; }"
        rules = parse(css)
        assert len(rules) == 1
        assert rules[0].declarations == {
            "color": "red",
            "font-size": "14px",
            "margin": "10px"
        }
    
    def test_multiline_declarations(self):
        css = """
        p {
            color: red;
            font-size: 14px;
            margin: 10px;
        }
        """
        rules = parse(css)
        assert len(rules) == 1
        assert rules[0].declarations == {
            "color": "red",
            "font-size": "14px",
            "margin": "10px"
        }
    
    def test_no_semicolon_on_last_declaration(self):
        css = "p { color: red; font-size: 14px }"
        rules = parse(css)
        assert rules[0].declarations == {
            "color": "red",
            "font-size": "14px"
        }
    
    def test_class_selector_rule(self):
        css = ".container { width: 100%; }"
        rules = parse(css)
        assert len(rules) == 1
        assert rules[0].selector.classes == ["container"]
        assert rules[0].declarations == {"width": "100%"}
    
    def test_id_selector_rule(self):
        css = "#header { height: 50px; }"
        rules = parse(css)
        assert len(rules) == 1
        assert rules[0].selector.id == "header"
        assert rules[0].declarations == {"height": "50px"}
    
    def test_compound_selector_rule(self):
        css = "div.container { padding: 20px; }"
        rules = parse(css)
        assert len(rules) == 1
        assert rules[0].selector.tag == "div"
        assert rules[0].selector.classes == ["container"]
    
    def test_whitespace_handling(self):
        css = "  p   {   color  :  red  ;  }  "
        rules = parse(css)
        assert len(rules) == 1
        assert rules[0].declarations == {"color": "red"}
    
    def test_comments(self):
        css = """
        /* This is a comment */
        p { color: red; }
        /* Another comment */
        div { /* inline comment */ background: blue; }
        """
        rules = parse(css)
        assert len(rules) == 2
        assert rules[0].selector.tag == "p"
        assert rules[1].selector.tag == "div"
    
    def test_property_values_with_spaces(self):
        css = "p { font-family: Arial, sans-serif; }"
        rules = parse(css)
        assert rules[0].declarations == {"font-family": "Arial, sans-serif"}
    
    def test_complex_stylesheet(self):
        css = """
        /* Reset */
        * { margin: 0; padding: 0; }
        
        body {
            font-family: Arial, sans-serif;
            font-size: 16px;
            color: #333;
        }
        
        h1 {
            font-size: 32px;
            margin-bottom: 20px;
        }
        
        .container {
            width: 960px;
            margin: 0 auto;
        }
        
        #header {
            background: #f0f0f0;
            padding: 10px;
        }
        
        div.highlight {
            background: yellow;
            font-weight: bold;
        }
        """
        rules = parse(css)
        assert len(rules) == 6
        
        # Check body rule
        body_rule = next(r for r in rules if r.selector.tag == "body")
        assert "font-family" in body_rule.declarations
        assert "font-size" in body_rule.declarations


class TestInlineStyleParser:
    """Test inline style attribute parsing."""
    
    def test_empty_style(self):
        decls = parse_inline_style("")
        assert decls == {}
    
    def test_single_declaration(self):
        decls = parse_inline_style("color: red")
        assert decls == {"color": "red"}
    
    def test_multiple_declarations(self):
        decls = parse_inline_style("color: red; font-size: 14px")
        assert decls == {"color": "red", "font-size": "14px"}
    
    def test_trailing_semicolon(self):
        decls = parse_inline_style("color: red; font-size: 14px;")
        assert decls == {"color": "red", "font-size": "14px"}
    
    def test_whitespace_handling(self):
        decls = parse_inline_style("  color : red  ;  font-size : 14px  ")
        assert decls == {"color": "red", "font-size": "14px"}
    
    def test_complex_values(self):
        decls = parse_inline_style("font-family: Arial, sans-serif; margin: 10px 20px")
        assert decls == {
            "font-family": "Arial, sans-serif",
            "margin": "10px 20px"
        }
    
    def test_malformed_ignored(self):
        # Missing colon
        decls = parse_inline_style("color red; font-size: 14px")
        assert decls == {"font-size": "14px"}


class TestComputedStyle:
    """Test computed style value accessors."""
    
    def test_empty_style(self):
        style = ComputedStyle()
        assert style.get("color") == ""
        assert style.get("color", "black") == "black"
    
    def test_get_set(self):
        style = ComputedStyle()
        style.set("color", "red")
        assert style.get("color") == "red"
    
    def test_get_int(self):
        style = ComputedStyle()
        style.set("font-size", "16px")
        assert style.get_int("font-size") == 16
    
    def test_get_int_no_unit(self):
        style = ComputedStyle()
        style.set("font-size", "16")
        assert style.get_int("font-size") == 16
    
    def test_get_int_default(self):
        style = ComputedStyle()
        assert style.get_int("font-size", 14) == 14
    
    def test_get_float(self):
        style = ComputedStyle()
        style.set("margin", "10.5px")
        assert style.get_float("margin") == 10.5
    
    def test_get_float_default(self):
        style = ComputedStyle()
        assert style.get_float("margin", 5.5) == 5.5


class TestStyleResolver:
    """Test style resolution with cascade and inheritance."""
    
    def test_default_styles(self):
        resolver = StyleResolver()
        elem = Element("p")
        style = resolver.resolve_style(elem)
        
        assert style.get("display") == "block"
        assert style.get("margin-top") == "16px"
        assert style.get("margin-bottom") == "16px"
    
    def test_no_default_for_unknown_tag(self):
        resolver = StyleResolver()
        elem = Element("unknown")
        style = resolver.resolve_style(elem)
        
        # Should have empty properties (no defaults)
        assert style.get("display") == ""
    
    def test_stylesheet_overrides_default(self):
        rules = parse("p { margin-top: 20px; }")
        resolver = StyleResolver(rules)
        elem = Element("p")
        style = resolver.resolve_style(elem)
        
        # Stylesheet should override default
        assert style.get("margin-top") == "20px"
        # But default not overridden should remain
        assert style.get("margin-bottom") == "16px"
    
    def test_inline_overrides_stylesheet(self):
        rules = parse("p { color: blue; }")
        resolver = StyleResolver(rules)
        elem = Element("p", {"style": "color: red"})
        style = resolver.resolve_style(elem)
        
        # Inline should win
        assert style.get("color") == "red"
    
    def test_specificity_class_over_tag(self):
        rules = parse("""
        p { color: blue; }
        .highlight { color: red; }
        """)
        resolver = StyleResolver(rules)
        elem = Element("p", {"class": "highlight"})
        style = resolver.resolve_style(elem)
        
        # Class selector has higher specificity
        assert style.get("color") == "red"
    
    def test_specificity_id_over_class(self):
        rules = parse("""
        p { color: blue; }
        .highlight { color: red; }
        #main { color: green; }
        """)
        resolver = StyleResolver(rules)
        elem = Element("p", {"class": "highlight", "id": "main"})
        style = resolver.resolve_style(elem)
        
        # ID selector has highest specificity
        assert style.get("color") == "green"
    
    def test_inheritance_from_parent(self):
        rules = parse("body { color: blue; font-size: 16px; }")
        resolver = StyleResolver(rules)
        
        parent = Element("body")
        parent_style = resolver.resolve_style(parent)
        
        child = Element("div")
        child_style = resolver.resolve_style(child, parent_style)
        
        # Should inherit color and font-size
        assert child_style.get("color") == "blue"
        assert child_style.get("font-size") == "16px"
    
    def test_non_inherited_properties(self):
        rules = parse("body { margin: 10px; }")
        resolver = StyleResolver(rules)
        
        parent = Element("body")
        parent_style = resolver.resolve_style(parent)
        
        child = Element("div")
        child_style = resolver.resolve_style(child, parent_style)
        
        # Margin should not inherit
        assert child_style.get("margin") == ""
    
    def test_child_overrides_inherited(self):
        rules = parse("""
        body { color: blue; }
        p { color: red; }
        """)
        resolver = StyleResolver(rules)
        
        parent = Element("body")
        parent_style = resolver.resolve_style(parent)
        
        child = Element("p")
        child_style = resolver.resolve_style(child, parent_style)
        
        # Child's own style should override inherited
        assert child_style.get("color") == "red"
    
    def test_resolve_tree(self):
        css = """
        body { color: blue; font-size: 16px; }
        p { margin: 10px; }
        .highlight { background: yellow; }
        """
        rules = parse(css)
        resolver = StyleResolver(rules)
        
        # Build tree
        root = Element("body")
        p1 = Element("p", parent=root)
        p2 = Element("p", {"class": "highlight"}, parent=root)
        text = Text("Hello", parent=p1)
        root.children = [p1, p2]
        p1.children = [text]
        
        # Resolve entire tree
        resolver.resolve_tree(root)
        
        # Check root
        assert root.computed_style.get("color") == "blue"
        assert root.computed_style.get("font-size") == "16px"
        
        # Check p1 (inherits color)
        assert p1.computed_style.get("color") == "blue"
        assert p1.computed_style.get("margin") == "10px"
        
        # Check p2 (inherits + has class)
        assert p2.computed_style.get("color") == "blue"
        assert p2.computed_style.get("background") == "yellow"
        
        # Check text (has parent style)
        assert text.computed_style.get("color") == "blue"
    
    def test_heading_defaults(self):
        resolver = StyleResolver()
        
        h1 = Element("h1")
        h1_style = resolver.resolve_style(h1)
        assert h1_style.get("font-size") == "32px"
        assert h1_style.get("font-weight") == "bold"
        
        h2 = Element("h2")
        h2_style = resolver.resolve_style(h2)
        assert h2_style.get("font-size") == "24px"
    
    def test_inline_elements(self):
        resolver = StyleResolver()
        
        a = Element("a")
        a_style = resolver.resolve_style(a)
        assert a_style.get("display") == "inline"
        assert a_style.get("color") == "blue"
        assert a_style.get("text-decoration") == "underline"
        
        span = Element("span")
        span_style = resolver.resolve_style(span)
        assert span_style.get("display") == "inline"

