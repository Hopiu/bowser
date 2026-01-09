"""Inline and text layout stubs."""


class TextLayout:
    def __init__(self, node, word, parent=None, previous=None):
        self.node = node
        self.word = word
        self.parent = parent
        self.previous = previous

    def layout(self):
        return len(self.word)
