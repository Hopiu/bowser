"""Compositing stubs."""


class CompositedLayer:
    def __init__(self, display_item=None):
        self.items = []
        if display_item:
            self.items.append(display_item)

    def add(self, display_item):
        self.items.append(display_item)
