"""Image loading and caching."""

import logging
import threading
from pathlib import Path
from typing import Optional, Callable
import skia

from .url import URL
from .http import request


logger = logging.getLogger("bowser.images")

# Path to assets directory (for about: pages)
ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"


class ImageCache:
    """Thread-safe global cache for loaded images."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._cache = {}
                cls._instance._failed = set()  # URLs that failed to load
                cls._instance._pending = set()  # URLs currently being loaded
                cls._instance._cache_lock = threading.Lock()
            return cls._instance

    def get(self, url: str) -> Optional[skia.Image]:
        """Get a cached image by URL."""
        with self._cache_lock:
            return self._cache.get(url)

    def set(self, url: str, image: skia.Image):
        """Cache an image by URL."""
        with self._cache_lock:
            self._cache[url] = image
            self._pending.discard(url)  # No longer pending

    def has(self, url: str) -> bool:
        """Check if URL is cached."""
        with self._cache_lock:
            return url in self._cache

    def mark_pending(self, url: str) -> bool:
        """Mark a URL as pending load. Returns False if already pending/cached/failed."""
        with self._cache_lock:
            if url in self._cache or url in self._failed or url in self._pending:
                return False
            self._pending.add(url)
            return True

    def mark_failed(self, url: str):
        """Mark a URL as failed to load (to prevent retries)."""
        with self._cache_lock:
            self._failed.add(url)
            self._pending.discard(url)  # No longer pending

    def has_failed(self, url: str) -> bool:
        """Check if URL previously failed to load."""
        with self._cache_lock:
            return url in self._failed

    def is_pending(self, url: str) -> bool:
        """Check if URL is currently being loaded."""
        with self._cache_lock:
            return url in self._pending

    def clear(self):
        """Clear all cached images."""
        with self._cache_lock:
            self._cache.clear()
            self._failed.clear()
            self._pending.clear()


# Callbacks for image load completion
ImageCallback = Callable[[Optional[skia.Image]], None]
# Callback for raw bytes (used internally for thread-safe loading)
BytesCallback = Callable[[Optional[bytes], str], None]


def get_cached_image(url: str, base_url: Optional[str] = None) -> Optional[skia.Image]:
    """
    Get an image from cache if available (no loading).

    Args:
        url: Image URL or file path
        base_url: Base URL for resolving relative URLs

    Returns:
        Cached Skia Image, or None if not in cache
    """
    full_url = _resolve_url(url, base_url)
    cache = ImageCache()
    return cache.get(full_url)


def has_image_failed(url: str, base_url: Optional[str] = None) -> bool:
    """
    Check if an image URL previously failed to load.

    Args:
        url: Image URL or file path
        base_url: Base URL for resolving relative URLs

    Returns:
        True if the URL failed to load previously
    """
    full_url = _resolve_url(url, base_url)
    cache = ImageCache()
    return cache.has_failed(full_url)


def is_data_url(url: str) -> bool:
    """Check if URL is a data: URL."""
    return url.startswith('data:')


def load_image(url: str, base_url: Optional[str] = None) -> Optional[skia.Image]:
    """
    Load an image from a URL or file path (synchronous).

    Args:
        url: Image URL or file path
        base_url: Base URL for resolving relative URLs

    Returns:
        Skia Image object, or None if loading failed
    """
    try:
        # Resolve the full URL first
        full_url = _resolve_url(url, base_url)

        # Check cache with resolved URL
        cache = ImageCache()
        cached = cache.get(full_url)
        if cached is not None:
            logger.debug(f"Image cache hit: {full_url}")
            return cached

        logger.info(f"Loading image: {full_url}")

        # Load raw bytes
        data = _load_image_bytes(full_url)
        if data is None:
            return None

        # Decode with Skia
        image = skia.Image.MakeFromEncoded(data)
        if image:
            # Convert to raster image for safe drawing
            # (encoded images may crash on some operations)
            image = image.makeRasterImage()
            cache.set(full_url, image)
            logger.debug(f"Loaded image: {full_url} ({image.width()}x{image.height()})")

        return image

    except Exception as e:
        logger.error(f"Failed to load image {url}: {e}")
        return None


def _load_image_bytes(full_url: str) -> Optional[bytes]:
    """Load raw image bytes from a URL or file path."""
    try:
        # Handle data URLs
        if full_url.startswith('data:'):
            return _load_data_url_bytes(full_url)

        # Handle file URLs
        if full_url.startswith('file://'):
            file_path = full_url[7:]  # Remove 'file://'
            return _load_file_bytes(file_path)

        # Handle HTTP/HTTPS URLs
        if full_url.startswith(('http://', 'https://')):
            return _load_http_bytes(full_url)

        # Try as local file path
        return _load_file_bytes(full_url)

    except Exception as e:
        logger.error(f"Failed to load image bytes from {full_url}: {e}")
        return None


def load_image_async(
    url: str,
    base_url: Optional[str] = None,
    on_complete: Optional[ImageCallback] = None,
    on_error: Optional[Callable[[Exception], None]] = None,
) -> int:
    """
    Load an image asynchronously in a background thread.

    Bytes are loaded in background, but Skia decoding happens on main thread
    to avoid threading issues with Skia objects.

    Args:
        url: Image URL or file path
        base_url: Base URL for resolving relative URLs
        on_complete: Callback with loaded image (or None if failed), called on main thread
        on_error: Callback with exception if loading failed, called on main thread

    Returns:
        Task ID that can be used to cancel the load
    """
    from .tasks import submit_task
    import gi
    gi.require_version("GLib", "2.0")
    from gi.repository import GLib

    # Resolve URL synchronously (fast operation)
    full_url = _resolve_url(url, base_url)

    # Check cache first (avoid thread overhead)
    cache = ImageCache()
    cached = cache.get(full_url)
    if cached is not None:
        logger.debug(f"Image cache hit: {full_url}")
        if on_complete:
            # Use GLib to call on main thread
            GLib.idle_add(lambda: on_complete(cached) or False)
        return -1  # No task needed

    # Atomically check if failed/pending and mark as pending
    # This prevents multiple concurrent loads of the same URL
    if not cache.mark_pending(full_url):
        logger.debug(f"Skipping image (cached/failed/pending): {full_url}")
        if on_complete:
            GLib.idle_add(lambda: on_complete(None) or False)
        return -1

    def do_load_bytes():
        """Load raw bytes in background thread."""
        return _load_image_bytes(full_url)

    def on_bytes_loaded(data: Optional[bytes]):
        """Decode image on main thread and call user callback."""
        if data is None:
            cache.mark_failed(full_url)
            if on_complete:
                on_complete(None)
            return

        try:
            # Decode image on main thread (Skia thread safety)
            decoded = skia.Image.MakeFromEncoded(data)
            if decoded:
                # Convert to raster image for safe drawing
                # (encoded images may crash on some operations)
                image = decoded.makeRasterImage()

                cache.set(full_url, image)
                logger.debug(f"Async loaded image: {full_url} ({image.width()}x{image.height()})")
                if on_complete:
                    on_complete(image)
            else:
                # Failed to decode (e.g., SVG or unsupported format)
                logger.warning(f"Failed to decode image (unsupported format?): {full_url}")
                cache.mark_failed(full_url)
                if on_complete:
                    on_complete(None)
        except Exception as e:
            logger.error(f"Failed to decode image {full_url}: {e}")
            cache.mark_failed(full_url)
            if on_complete:
                on_complete(None)
            if on_complete:
                on_complete(None)

    # Always use on_bytes_loaded to ensure caching happens
    return submit_task(do_load_bytes, on_bytes_loaded, on_error)


def _resolve_url(url: str, base_url: Optional[str]) -> str:
    """Resolve a potentially relative URL against a base URL."""
    # Already absolute
    if url.startswith(('http://', 'https://', 'data:', 'file://')):
        return url

    # Handle about: pages - resolve relative to assets directory
    if base_url and base_url.startswith('about:'):
        # For about: pages, resolve relative to the assets/pages directory
        pages_dir = ASSETS_DIR / "pages"
        # Use Path to properly resolve .. paths
        resolved_path = (pages_dir / url).resolve()
        if resolved_path.exists():
            return str(resolved_path)
        # Also check assets root directly
        asset_path = (ASSETS_DIR / url).resolve()
        if asset_path.exists():
            return str(asset_path)
        # Return resolved path even if not found (will fail later with proper error)
        return str(resolved_path)

    # No base URL - treat as local file
    if not base_url:
        return url

    # Use URL class for proper resolution
    try:
        base = URL(base_url)
        resolved = base.resolve(url)
        return str(resolved)
    except Exception:
        # Fallback: simple concatenation
        if base_url.endswith('/'):
            return base_url + url
        else:
            # Remove the last path component
            base_parts = base_url.rsplit('/', 1)
            if len(base_parts) > 1 and '/' in base_parts[0]:
                return base_parts[0] + '/' + url
            return url


def _load_file_bytes(file_path: str) -> Optional[bytes]:
    """Load raw bytes from a local file."""
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        logger.debug(f"Loaded {len(data)} bytes from file: {file_path}")
        return data
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        return None


def _load_http_bytes(url: str) -> Optional[bytes]:
    """Load raw bytes from HTTP/HTTPS URL."""
    try:
        url_obj = URL(url)
        status, content_type, body = request(url_obj)

        if status != 200:
            logger.warning(f"HTTP {status} when loading image: {url}")
            return None

        logger.debug(f"Loaded {len(body)} bytes from HTTP: {url}")
        return body

    except Exception as e:
        logger.error(f"Failed to load from HTTP {url}: {e}")
        return None


def _load_data_url_bytes(data_url: str) -> Optional[bytes]:
    """Extract raw bytes from a data: URL."""
    try:
        # Parse data URL: data:[<mediatype>][;base64],<data>
        if not data_url.startswith('data:'):
            return None

        # Split off the 'data:' prefix
        _, rest = data_url.split(':', 1)

        # Split metadata from data
        if ',' not in rest:
            return None

        metadata, data = rest.split(',', 1)

        # Check if base64 encoded
        if ';base64' in metadata:
            import base64
            decoded = base64.b64decode(data)
        else:
            # URL-encoded data
            import urllib.parse
            decoded = urllib.parse.unquote(data).encode('utf-8')

        logger.debug(f"Extracted {len(decoded)} bytes from data URL")
        return decoded

    except Exception as e:
        logger.error(f"Failed to parse data URL: {e}")
        return None


def _load_from_http(url: str) -> Optional[skia.Image]:
    """Load an image from HTTP/HTTPS URL."""
    try:
        url_obj = URL(url)
        status, content_type, body = request(url_obj)

        if status != 200:
            logger.warning(f"HTTP {status} when loading image: {url}")
            return None

        # Decode image from bytes
        image = skia.Image.MakeFromEncoded(body)

        if image:
            # Cache it
            cache = ImageCache()
            cache.set(url, image)
            logger.debug(f"Loaded image from HTTP: {url} ({image.width()}x{image.height()})")

        return image

    except Exception as e:
        logger.error(f"Failed to load image from HTTP {url}: {e}")
        return None


def _load_from_file(file_path: str) -> Optional[skia.Image]:
    """Load an image from a local file."""
    try:
        with open(file_path, 'rb') as f:
            data = f.read()

        image = skia.Image.MakeFromEncoded(data)

        if image:
            # Cache it
            cache = ImageCache()
            cache.set(file_path, image)
            logger.debug(f"Loaded image from file: {file_path} ({image.width()}x{image.height()})")

        return image

    except Exception as e:
        logger.error(f"Failed to load image from file {file_path}: {e}")
        return None


def _load_data_url(data_url: str) -> Optional[skia.Image]:
    """Load an image from a data: URL."""
    try:
        # Parse data URL: data:[<mediatype>][;base64],<data>
        if not data_url.startswith('data:'):
            return None

        # Split off the 'data:' prefix
        _, rest = data_url.split(':', 1)

        # Split metadata from data
        if ',' not in rest:
            return None

        metadata, data = rest.split(',', 1)

        # Check if base64 encoded
        if ';base64' in metadata:
            import base64
            decoded = base64.b64decode(data)
        else:
            # URL-encoded data
            import urllib.parse
            decoded = urllib.parse.unquote(data).encode('utf-8')

        image = skia.Image.MakeFromEncoded(decoded)

        if image:
            # Don't cache data URLs (they're already embedded)
            logger.debug(f"Loaded image from data URL ({image.width()}x{image.height()})")

        return image

    except Exception as e:
        logger.error(f"Failed to load image from data URL: {e}")
        return None
