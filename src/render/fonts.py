"""Font management with Skia."""

import skia


class FontCache:
    """Cache for Skia fonts and typefaces."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._font_cache = {}
            cls._instance._default_typeface = None
        return cls._instance
    
    def get_typeface(self):
        """Get the default typeface, creating it if needed."""
        if self._default_typeface is None:
            self._default_typeface = skia.Typeface.MakeDefault()
        return self._default_typeface
    
    def get_font(self, size: int, weight: str = "normal", style: str = "normal") -> skia.Font:
        """Get a cached Skia font for the given parameters."""
        key = (size, weight, style)
        if key not in self._font_cache:
            typeface = self.get_typeface()
            self._font_cache[key] = skia.Font(typeface, size)
        return self._font_cache[key]
    
    def measure_text(self, text: str, font: skia.Font) -> float:
        """Measure the width of text using the given font."""
        return font.measureText(text)
    
    def get_line_height(self, font_size: int) -> float:
        """Get the line height for a given font size."""
        return font_size * 1.4


# Global font cache instance
_font_cache = FontCache()


def get_font(size: int, weight: str = "normal", style: str = "normal") -> skia.Font:
    """Get a cached font."""
    return _font_cache.get_font(size, weight, style)


def measure_text(text: str, size: int) -> float:
    """Measure text width at given font size."""
    font = get_font(size)
    return _font_cache.measure_text(text, font)


def linespace(font_size: int) -> float:
    """Get line height for font size."""
    return _font_cache.get_line_height(font_size)
