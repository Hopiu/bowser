"""JavaScript context integration (stub)."""


class JSContext:
    def __init__(self, tab, url_origin: str):
        self.tab = tab
        self.url_origin = url_origin

    def run(self, script: str, code: str, window_id=0):
        # Placeholder: wire to QuickJS/NG binding
        return None
