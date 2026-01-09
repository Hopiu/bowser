"""CSS parser stubs."""


class CSSRule:
    def __init__(self, selector: str, declarations: dict):
        self.selector = selector
        self.declarations = declarations


def parse(css_text: str):
    # Placeholder: split on semicolons per line
    rules = []
    for line in css_text.splitlines():
        if "{" not in line:
            continue
    return rules
