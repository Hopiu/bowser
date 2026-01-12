"""Tests for HTML parsing."""

from src.parser.html import Text, Element, print_tree


class TestHTMLElements:
    def test_text_node(self):
        text = Text("Hello World")
        assert text.text == "Hello World"
        assert text.parent is None

    def test_text_node_with_parent(self):
        parent = Element("div")
        text = Text("Hello", parent=parent)
        assert text.parent is parent

    def test_element_node(self):
        elem = Element("div", {"class": "container"})
        assert elem.tag == "div"
        assert elem.attributes == {"class": "container"}
        assert elem.children == []

    def test_element_default_attributes(self):
        elem = Element("p")
        assert elem.attributes == {}

    def test_element_parent(self):
        parent = Element("body")
        child = Element("div", parent=parent)
        assert child.parent is parent


class TestPrintTree:
    def test_print_single_element(self, capsys):
        elem = Element("div")
        print_tree(elem)
        captured = capsys.readouterr()
        assert "Element('div'" in captured.out

    def test_print_tree_with_children(self, capsys):
        root = Element("html")
        body = Element("body", parent=root)
        text = Text("Hello", parent=body)
        root.children = [body]
        body.children = [text]

        print_tree(root)
        captured = capsys.readouterr()
        assert "Element('html'" in captured.out
        assert "Element('body'" in captured.out
        assert "Text('Hello')" in captured.out
