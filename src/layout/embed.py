"""Embedded content layout (images, iframes)."""

import logging
from typing import Optional, Callable
import skia

from ..network.images import load_image, load_image_async, get_cached_image, is_data_url, has_image_failed


logger = logging.getLogger("bowser.layout.embed")


# Callback type for when an image finishes loading
OnImageLoadedCallback = Callable[["ImageLayout"], None]


class ImageLayout:
    """Layout for an <img> element."""

    # Global callback for image load completion (set by render pipeline)
    _on_any_image_loaded: Optional[Callable[[], None]] = None

    def __init__(self, node, parent=None, previous=None, frame=None):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.frame = frame
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.image: Optional[skia.Image] = None
        self.alt_text = ""
        self.is_inline = True  # Images are inline by default
        self._loading = False
        self._load_task_id: Optional[int] = None
        self._src = ""
        self._base_url: Optional[str] = None
        self._max_width: Optional[float] = None  # Store max_width for async re-layout

    def load(self, base_url: Optional[str] = None, async_load: bool = False):
        """
        Load the image from the src attribute.

        Args:
            base_url: Base URL for resolving relative paths
            async_load: If True, load in background thread (non-blocking)
        """
        if not hasattr(self.node, 'attributes'):
            return

        src = self.node.attributes.get('src', '')
        if not src:
            logger.warning("Image element has no src attribute")
            return

        # Get alt text
        self.alt_text = self.node.attributes.get('alt', '')
        self._src = src
        self._base_url = base_url

        # Check cache first (fast, non-blocking)
        cached = get_cached_image(src, base_url)
        if cached:
            self.image = cached
            return

        # Skip images that previously failed to load (e.g., SVG)
        if has_image_failed(src, base_url):
            return

        # Data URLs should be loaded synchronously (they're inline, no network)
        if is_data_url(src):
            self.image = load_image(src, base_url)
            return

        if async_load:
            # Load in background thread
            self._load_async(src, base_url)
        else:
            # Synchronous load (blocks UI - use sparingly)
            self.image = load_image(src, base_url)

    def _load_async(self, src: str, base_url: Optional[str]):
        """Load image asynchronously."""
        self._loading = True

        def on_complete(image: Optional[skia.Image]):
            self._loading = False
            self.image = image
            if image:
                # Recalculate layout with actual dimensions
                self._update_dimensions()
                logger.debug(f"Async loaded image: {src} ({image.width()}x{image.height()})")
            # Trigger re-render
            if ImageLayout._on_any_image_loaded:
                ImageLayout._on_any_image_loaded()

        def on_error(e: Exception):
            self._loading = False
            logger.error(f"Async image load failed: {src}: {e}")

        self._load_task_id = load_image_async(src, base_url, on_complete, on_error)

    def _update_dimensions(self):
        """Update dimensions based on loaded image."""
        if not self.image:
            return

        # Get explicit width/height attributes
        width_attr = self.node.attributes.get('width', '') if hasattr(self.node, 'attributes') else ''
        height_attr = self.node.attributes.get('height', '') if hasattr(self.node, 'attributes') else ''

        intrinsic_width = self.image.width()
        intrinsic_height = self.image.height()

        # Calculate dimensions based on attributes or intrinsic size
        if width_attr and height_attr:
            try:
                self.width = float(width_attr)
                self.height = float(height_attr)
            except ValueError:
                self.width = intrinsic_width
                self.height = intrinsic_height
        elif width_attr:
            try:
                self.width = float(width_attr)
                if intrinsic_width > 0:
                    aspect_ratio = intrinsic_height / intrinsic_width
                    self.height = self.width * aspect_ratio
                else:
                    self.height = intrinsic_height
            except ValueError:
                self.width = intrinsic_width
                self.height = intrinsic_height
        elif height_attr:
            try:
                self.height = float(height_attr)
                if intrinsic_height > 0:
                    aspect_ratio = intrinsic_width / intrinsic_height
                    self.width = self.height * aspect_ratio
                else:
                    self.width = intrinsic_width
            except ValueError:
                self.width = intrinsic_width
                self.height = intrinsic_height
        else:
            self.width = intrinsic_width
            self.height = intrinsic_height

        # Apply max_width constraint if set
        if self._max_width and self.width > self._max_width:
            aspect_ratio = intrinsic_height / intrinsic_width if intrinsic_width > 0 else 1
            self.width = self._max_width
            self.height = self.width * aspect_ratio

    @property
    def is_loading(self) -> bool:
        """True if image is currently being loaded."""
        return self._loading

    def cancel_load(self):
        """Cancel any pending async load."""
        if self._load_task_id is not None:
            from ..network.tasks import cancel_task
            cancel_task(self._load_task_id)
            self._load_task_id = None
            self._loading = False

    def layout(self, max_width: Optional[float] = None):
        """
        Calculate the layout dimensions for this image.

        Returns:
            Width of the image (for inline layout)
        """
        # Store max_width for async image load re-layout
        self._max_width = max_width

        if not self.image:
            # If image failed to load, use alt text dimensions
            # For now, just use a placeholder size
            self.width = 100
            self.height = 100
            return self.width

        # Get explicit width/height attributes
        width_attr = self.node.attributes.get('width', '') if hasattr(self.node, 'attributes') else ''
        height_attr = self.node.attributes.get('height', '') if hasattr(self.node, 'attributes') else ''

        # Get intrinsic dimensions
        intrinsic_width = self.image.width()
        intrinsic_height = self.image.height()

        # Calculate display dimensions
        if width_attr and height_attr:
            # Both specified
            try:
                self.width = float(width_attr)
                self.height = float(height_attr)
            except ValueError:
                self.width = intrinsic_width
                self.height = intrinsic_height
        elif width_attr:
            # Only width specified - maintain aspect ratio
            try:
                self.width = float(width_attr)
                if intrinsic_width > 0:
                    aspect_ratio = intrinsic_height / intrinsic_width
                    self.height = self.width * aspect_ratio
                else:
                    self.height = intrinsic_height
            except ValueError:
                self.width = intrinsic_width
                self.height = intrinsic_height
        elif height_attr:
            # Only height specified - maintain aspect ratio
            try:
                self.height = float(height_attr)
                if intrinsic_height > 0:
                    aspect_ratio = intrinsic_width / intrinsic_height
                    self.width = self.height * aspect_ratio
                else:
                    self.width = intrinsic_width
            except ValueError:
                self.width = intrinsic_width
                self.height = intrinsic_height
        else:
            # No dimensions specified - use intrinsic size
            self.width = intrinsic_width
            self.height = intrinsic_height

        # Always constrain to max_width if specified (applies to all cases)
        if max_width and self.width > max_width:
            aspect_ratio = intrinsic_height / intrinsic_width if intrinsic_width > 0 else 1
            self.width = max_width
            self.height = self.width * aspect_ratio

        return self.width


class IframeLayout:
    def __init__(self, node, parent=None, previous=None, parent_frame=None):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.parent_frame = parent_frame

    def layout(self):
        return 0
