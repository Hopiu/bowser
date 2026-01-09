"""HTML parser stubs."""


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
