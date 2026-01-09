"""Font management stubs."""


def get_font(size: int, weight: str = "normal", style: str = "normal"):
    return (size, weight, style)


def linespace(font) -> int:
    size, _, _ = font
    return int(size * 1.2)
