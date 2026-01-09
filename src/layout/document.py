"""Document-level layout stub."""


class DocumentLayout:
    def __init__(self, node, frame=None):
        self.node = node
        self.frame = frame
        self.children = []

    def layout(self, width: int, zoom: float = 1.0):
        # Placeholder layout logic
        return width * zoom
