"""Browser chrome (GTK UI)."""

import gi
from typing import Optional
import logging

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GdkPixbuf
from functools import partial

import skia


class Chrome:
    def __init__(self, browser):
        self.logger = logging.getLogger("bowser.chrome")
        self.browser = browser
        self.window: Optional[Gtk.ApplicationWindow] = None
        self.address_bar: Optional[Gtk.Entry] = None
        self.back_btn: Optional[Gtk.Button] = None
        self.forward_btn: Optional[Gtk.Button] = None
        self.reload_btn: Optional[Gtk.Button] = None
        self.go_btn: Optional[Gtk.Button] = None
        self.drawing_area: Optional[Gtk.DrawingArea] = None
        self.tabs_box: Optional[Gtk.Box] = None
        self.skia_surface: Optional[skia.Surface] = None

    def create_window(self):
        """Initialize the GTK application window."""
        self.window = Gtk.ApplicationWindow(application=self.browser.app)
        self.window.set_default_size(1024, 768)
        self.window.set_title("Bowser")

        # Main vertical box
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.window.set_child(vbox)

        # Top bar: address bar + buttons
        top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        top_bar.set_margin_top(5)
        top_bar.set_margin_bottom(5)
        top_bar.set_margin_start(5)
        top_bar.set_margin_end(5)

        self.back_btn = Gtk.Button(label="◀")
        self.forward_btn = Gtk.Button(label="▶")
        self.reload_btn = Gtk.Button(label="⟳")

        self.address_bar = Gtk.Entry()
        self.address_bar.set_text("https://example.com")
        self.address_bar.set_hexpand(True)

        self.go_btn = Gtk.Button(label="Go")

        top_bar.append(self.back_btn)
        top_bar.append(self.forward_btn)
        top_bar.append(self.reload_btn)
        top_bar.append(self.address_bar)
        top_bar.append(self.go_btn)

        vbox.append(top_bar)

        # Tabs bar: contains tab buttons and a new-tab button
        self.tabs_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.tabs_box.set_margin_start(5)
        self.tabs_box.set_margin_end(5)
        self.tabs_box.set_margin_bottom(4)
        vbox.append(self.tabs_box)

        # Drawing area for content
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_vexpand(True)
        self.drawing_area.set_hexpand(True)
        self.drawing_area.set_draw_func(self.on_draw)
        vbox.append(self.drawing_area)

        # Status bar
        status_bar = Gtk.Label(label="Ready")
        status_bar.set_xalign(0)
        status_bar.set_margin_start(5)
        vbox.append(status_bar)

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

        # Draw placeholder text
        paint = skia.Paint()
        paint.setAntiAlias(True)
        paint.setColor(skia.ColorBLACK)
        font = skia.Font(skia.Typeface.MakeDefault(), 20)
        canvas.drawString("Bowser — M1: Hello World", 20, 50, font, paint)

        # Paint render stats
        canvas.drawString(f"Window: {width}x{height}", 20, 80, font, paint)

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

    def paint(self):
        """Trigger redraw of the drawing area."""
        if self.drawing_area:
            self.drawing_area.queue_draw()
