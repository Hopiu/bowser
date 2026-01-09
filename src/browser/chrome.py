"""Browser chrome (Adwaita UI)."""

import gi
from typing import Optional
import logging
from functools import partial

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Gdk, GdkPixbuf, Adw
import skia


class Chrome:
    def __init__(self, browser):
        self.logger = logging.getLogger("bowser.chrome")
        self.browser = browser
        self.window: Optional[Adw.ApplicationWindow] = None
        self.address_bar: Optional[Gtk.Entry] = None
        self.back_btn: Optional[Gtk.Button] = None
        self.forward_btn: Optional[Gtk.Button] = None
        self.reload_btn: Optional[Gtk.Button] = None
        self.go_btn: Optional[Gtk.Button] = None
        self.drawing_area: Optional[Gtk.DrawingArea] = None
        self.tabs_box: Optional[Gtk.Box] = None
        self.skia_surface: Optional[skia.Surface] = None

    def create_window(self):
        """Initialize the Adwaita application window."""
        # Initialize Adwaita application
        if not hasattr(self.browser.app, '_adw_init'):
            Adw.init()
            self.browser.app._adw_init = True
        
        # Create Adwaita window instead of standard GTK window
        self.window = Adw.ApplicationWindow(application=self.browser.app)
        self.window.set_default_size(1024, 768)
        self.window.set_title("Bowser")

        # Main vertical box for the window structure
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.window.set_content(vbox)

        # Header bar with navigation and address bar
        header_bar = Gtk.HeaderBar()
        vbox.append(header_bar)
        
        # Navigation buttons in header bar
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        nav_box.add_css_class("linked")
        
        self.back_btn = Gtk.Button(label="◀")
        self.back_btn.set_tooltip_text("Back")
        self.forward_btn = Gtk.Button(label="▶")
        self.forward_btn.set_tooltip_text("Forward")
        self.reload_btn = Gtk.Button(label="⟳")
        self.reload_btn.set_tooltip_text("Reload")
        
        nav_box.append(self.back_btn)
        nav_box.append(self.forward_btn)
        nav_box.append(self.reload_btn)
        header_bar.pack_start(nav_box)
        
        # Address bar - centered in header
        self.address_bar = Gtk.Entry()
        self.address_bar.set_placeholder_text("Enter URL...")
        self.address_bar.set_hexpand(True)
        self.address_bar.set_max_width_chars(40)
        header_bar.set_title_widget(self.address_bar)
        
        # Go button in header bar end
        self.go_btn = Gtk.Button(label="Go")
        self.go_btn.add_css_class("suggested-action")
        header_bar.pack_end(self.go_btn)

        # Tabs bar: contains tab buttons and a new-tab button
        self.tabs_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.tabs_box.set_margin_start(8)
        self.tabs_box.set_margin_end(8)
        self.tabs_box.set_margin_top(6)
        self.tabs_box.set_margin_bottom(6)
        
        tabs_frame = Gtk.Frame()
        tabs_frame.set_child(self.tabs_box)
        vbox.append(tabs_frame)

        # Drawing area for content
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_vexpand(True)
        self.drawing_area.set_hexpand(True)
        self.drawing_area.set_draw_func(self.on_draw)
        vbox.append(self.drawing_area)

        # Status bar with Adwaita styling
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        status_box.add_css_class("toolbar")
        status_bar = Gtk.Label(label="Ready")
        status_bar.set_xalign(0)
        status_bar.set_margin_start(8)
        status_bar.set_margin_end(8)
        status_box.append(status_bar)
        vbox.append(status_box)

        self.window.present()
        # Build initial tab bar now that window exists
        self.rebuild_tab_bar()

        # Wire handlers
        if self.address_bar:
            self.address_bar.connect("activate", self._on_addressbar_activate)
        if self.go_btn:
            self.go_btn.connect("clicked", self._on_go_clicked)
        if self.back_btn:
            self.back_btn.connect("clicked", lambda _b: self.browser.go_back())
        if self.forward_btn:
            self.forward_btn.connect("clicked", lambda _b: self.browser.go_forward())
        if self.reload_btn:
            self.reload_btn.connect("clicked", lambda _b: self.browser.reload())

    def _clear_children(self, box: Gtk.Box):
        child = box.get_first_child()
        while child is not None:
            nxt = child.get_next_sibling()
            box.remove(child)
            child = nxt

    def rebuild_tab_bar(self):
        """Recreate tab buttons to reflect current tabs and active tab."""
        if not self.tabs_box:
            return
        self._clear_children(self.tabs_box)

        # Add a button per tab with a close '×' control
        for i, tab in enumerate(self.browser.tabs):
            # Composite tab widget: label button + inline close button in one container
            tab_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
            tab_container.add_css_class("linked")  # visual integration

            label = f"{i+1}: {tab.title}"
            tab_btn = Gtk.Button(label=label)
            tab_btn.set_hexpand(False)
            if tab is self.browser.active_tab:
                tab_btn.add_css_class("suggested-action")
            tab_btn.connect("clicked", partial(self.browser.set_active_tab, tab))

            close_btn = Gtk.Button(label="×")
            close_btn.add_css_class("flat")
            close_btn.connect("clicked", partial(self.browser.close_tab, tab))

            tab_container.append(tab_btn)
            tab_container.append(close_btn)
            self.tabs_box.append(tab_container)

        # New tab '+' button at the end
        plus_btn = Gtk.Button(label="+")
        plus_btn.connect("clicked", lambda _b: self.browser.new_tab("https://example.com"))
        self.tabs_box.append(plus_btn)

    def update_address_bar(self):
        if not self.address_bar:
            return
        url = None
        if self.browser.active_tab and self.browser.active_tab.current_url:
            url = str(self.browser.active_tab.current_url)
        self.address_bar.set_text(url or "")

    # Handlers
    def _on_addressbar_activate(self, entry: Gtk.Entry):
        self.browser.navigate_to(entry.get_text())

    def _on_go_clicked(self, _btn: Gtk.Button):
        if self.address_bar:
            self.browser.navigate_to(self.address_bar.get_text())

    def on_draw(self, drawing_area, context, width, height):
        """Callback for drawing the content area using Skia."""
        self.logger.debug(f"on_draw start {width}x{height}")
        # Create Skia surface for this frame
        self.skia_surface = skia.Surface(width, height)
        canvas = self.skia_surface.getCanvas()

        # White background
        canvas.clear(skia.ColorWHITE)

        # Get content to render
        content_text = self._get_content_text()
        
        if content_text:
            # Render actual page content with text wrapping
            self._render_text_content(canvas, content_text, width, height)
        else:
            # Show placeholder
            paint = skia.Paint()
            paint.setAntiAlias(True)
            paint.setColor(skia.ColorBLACK)
            font = skia.Font(skia.Typeface.MakeDefault(), 20)
            canvas.drawString("Bowser — Enter a URL to browse", 20, 50, font, paint)

        # Convert Skia surface to GTK Pixbuf and blit to Cairo context
        image = self.skia_surface.makeImageSnapshot()
        png_data = image.encodeToData().bytes()

        # Load PNG data into a Pixbuf
        from io import BytesIO

        loader = GdkPixbuf.PixbufLoader.new_with_type("png")
        loader.write(png_data)
        loader.close()
        pixbuf = loader.get_pixbuf()

        # Render pixbuf to Cairo context
        Gdk.cairo_set_source_pixbuf(context, pixbuf, 0, 0)
        context.paint()
        self.logger.debug("on_draw end")
    
    def _get_content_text(self) -> str:
        """Extract text content from active tab's document."""
        if not self.browser.active_tab:
            return ""
        
        frame = self.browser.active_tab.main_frame
        if not frame.document:
            return ""
        
        # Extract text from document tree
        return self._extract_text(frame.document)
    
    def _extract_text(self, node) -> str:
        """Recursively extract text from HTML tree."""
        from ..parser.html import Text, Element
        
        if isinstance(node, Text):
            return node.text
        elif isinstance(node, Element):
            texts = []
            for child in node.children:
                texts.append(self._extract_text(child))
            return " ".join(texts)
        return ""
    
    def _render_text_content(self, canvas, text: str, width: int, height: int):
        """Render text content with basic word wrapping."""
        paint = skia.Paint()
        paint.setAntiAlias(True)
        paint.setColor(skia.ColorBLACK)
        
        font_size = 14
        font = skia.Font(skia.Typeface.MakeDefault(), font_size)
        
        # Simple word wrapping
        words = text.split()
        lines = []
        current_line = []
        current_width = 0
        max_width = width - 40  # 20px margin on each side
        
        for word in words:
            word_width = font.measureText(word + " ")
            
            if current_width + word_width > max_width and current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_width = word_width
            else:
                current_line.append(word)
                current_width += word_width
        
        if current_line:
            lines.append(" ".join(current_line))
        
        # Draw lines
        y = 30
        line_height = font_size * 1.4
        
        for line in lines:
            if y > height - 20:  # Don't draw past bottom
                break
            canvas.drawString(line, 20, y, font, paint)
            y += line_height

    def paint(self):
        """Trigger redraw of the drawing area."""
        if self.drawing_area:
            self.drawing_area.queue_draw()
