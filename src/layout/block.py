"""Block and line layout stubs."""


class BlockLayout:
    def __init__(self, node, parent=None, previous=None, frame=None):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.frame = frame
        self.children = []

    def layout(self):
        return 0


class LineLayout:
    def __init__(self, node, parent=None, previous=None):
        self.node = node
        self.parent = parent
        self.previous = previous

    def layout(self):
        return 0
