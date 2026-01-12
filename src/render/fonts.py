"""Font management with Skia, honoring CSS font-family lists."""

from typing import Iterable, Optional, Tuple

import skia


def _normalize_family_list(family: Optional[str | Iterable[str]]) -> Tuple[str, ...]:
    """Normalize a CSS font-family string or iterable into a tuple of names."""
    if family is None:
        return tuple()

    if isinstance(family, str):
        candidates = [part.strip().strip('"\'') for part in family.split(",") if part.strip()]
    else:
        candidates = [str(part).strip().strip('"\'') for part in family if str(part).strip()]

    # Remove empties while preserving order
    return tuple(name for name in candidates if name)


class FontCache:
    """Cache for Skia fonts and typefaces."""

    _instance = None
    
    # Common emoji/symbol fonts to try as last resort before showing tofu
    _EMOJI_FALLBACK_FONTS = (
        'Noto Color Emoji',
        'Apple Color Emoji',
        'Segoe UI Emoji',
        'Segoe UI Symbol',
        'Noto Emoji',
        'Android Emoji',
    )

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._font_cache = {}
            cls._instance._typeface_cache = {}
            cls._instance._default_typeface = skia.Typeface.MakeDefault()
        return cls._instance

    def _load_typeface_for_text(self, families: Tuple[str, ...], text: str) -> skia.Typeface:
        """Return the first typeface from the family list that can render the text."""
        if not families:
            return self._default_typeface

        # Simplified cache key: is it emoji or regular text?
        # This dramatically reduces cache entries and font lookups
        is_emoji = text and self._is_emoji_char(text[0])
        cache_key = (families, is_emoji)
        
        if cache_key in self._typeface_cache:
            return self._typeface_cache[cache_key]

        # Try each family until we find one that has glyphs for the text
        for family in families:
            # Skip generic families that won't resolve to specific fonts
            if family.lower() in ('serif', 'sans-serif', 'monospace', 'cursive', 'fantasy'):
                continue
                
            typeface = skia.Typeface.MakeFromName(family, skia.FontStyle.Normal())
            if typeface and typeface.getFamilyName() == family:
                # Font was actually found - check if it has glyphs for sample text
                if text and self._has_glyphs(typeface, text):
                    self._typeface_cache[cache_key] = typeface
                    return typeface

        # Nothing in the CSS font-family worked. If this is emoji, try common emoji fonts
        # as a last resort to avoid showing tofu squares
        if is_emoji:
            for fallback_font in self._EMOJI_FALLBACK_FONTS:
                typeface = skia.Typeface.MakeFromName(fallback_font, skia.FontStyle.Normal())
                if typeface and typeface.getFamilyName() == fallback_font:
                    if self._has_glyphs(typeface, text):
                        self._typeface_cache[cache_key] = typeface
                        return typeface

        # Nothing matched, use default (will show tofu for unsupported characters)
        self._typeface_cache[cache_key] = self._default_typeface
        return self._default_typeface

    def _is_emoji_char(self, char: str) -> bool:
        """Check if a character is likely an emoji based on Unicode range."""
        code = ord(char)
        # Common emoji ranges (simplified check)
        return (
            0x1F300 <= code <= 0x1F9FF or  # Emoticons, symbols, pictographs
            0x2600 <= code <= 0x26FF or    # Miscellaneous symbols
            0x2700 <= code <= 0x27BF or    # Dingbats
            0xFE00 <= code <= 0xFE0F or    # Variation selectors
            0x1F000 <= code <= 0x1F02F or  # Mahjong, domino tiles
            0x1F0A0 <= code <= 0x1F0FF     # Playing cards
        )

    def _has_glyphs(self, typeface: skia.Typeface, text: str) -> bool:
        """Check if the typeface has glyphs for the given text (sample first char only for speed)."""
        # Only check first character for performance - good enough for font selection
        if not text:
            return False
        return typeface.unicharToGlyph(ord(text[0])) != 0

    def get_font(
        self,
        size: int,
        family: Optional[str | Iterable[str]] = None,
        weight: str = "normal",
        style: str = "normal",
        text: str = "",
    ) -> skia.Font:
        """Get a cached Skia font for the given parameters."""
        families = _normalize_family_list(family)
        # Simplified cache: emoji vs non-emoji, not per-character
        is_emoji = text and self._is_emoji_char(text[0])
        key = (size, families, weight, style, is_emoji)
        if key not in self._font_cache:
            typeface = self._load_typeface_for_text(families, text)
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


def get_font(
    size: int,
    family: Optional[str | Iterable[str]] = None,
    weight: str = "normal",
    style: str = "normal",
    text: str = "",
) -> skia.Font:
    """Get a cached font, honoring the provided font-family list when possible."""
    return _font_cache.get_font(size, family, weight, style, text)


def measure_text(text: str, size: int, family: Optional[str | Iterable[str]] = None) -> float:
    """Measure text width at given font size and family."""
    font = get_font(size, family, text=text)
    return _font_cache.measure_text(text, font)


def linespace(font_size: int) -> float:
    """Get line height for font size."""
    return _font_cache.get_line_height(font_size)
