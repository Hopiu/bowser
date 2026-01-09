"""Accessibility stubs."""


class AccessibilityNode:
    def __init__(self, node, parent=None):
        self.node = node
        self.parent = parent

    def build(self):
        return self
