"""Embedded content layout stubs (images, iframes)."""


class ImageLayout:
    def __init__(self, node, parent=None, previous=None, frame=None):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.frame = frame

    def layout(self):
        return 0


class IframeLayout:
    def __init__(self, node, parent=None, previous=None, parent_frame=None):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.parent_frame = parent_frame

    def layout(self):
        return 0
