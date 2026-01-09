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
        self.tab_view: Optional[Adw.TabView] = None
        self.tab_bar: Optional[Adw.TabBar] = None
        self.skia_surface: Optional[skia.Surface] = None
        self.tab_pages: dict = {}  # Map tab objects to AdwTabPage
        self._closing_tabs: set = set()  # Track tabs being closed to prevent re-entry

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

        # Create TabView for managing tabs
        self.tab_view = Adw.TabView()
        
        # Create TabBar for tab display
        self.tab_bar = Adw.TabBar()
        self.tab_bar.set_view(self.tab_view)
        self.tab_bar.set_autohide(False)
        
        # Add New Tab button to the tab bar
        new_tab_btn = Gtk.Button()
        new_tab_btn.set_icon_name("list-add-symbolic")
        new_tab_btn.set_tooltip_text("New Tab")
        new_tab_btn.connect("clicked", lambda _: self.browser.new_tab("about:startpage"))
        self.tab_bar.set_end_action_widget(new_tab_btn)
        
        vbox.append(self.tab_bar)
        
        # Create a container box for content that will hold the drawing area
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_vexpand(True)
        content_box.set_hexpand(True)
        
        # Create the drawing area for rendering page content
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_vexpand(True)
        self.drawing_area.set_hexpand(True)
        self.drawing_area.set_draw_func(self.on_draw)
        content_box.append(self.drawing_area)
        
        # Add content box to vbox (not to TabView - we use a single drawing area for all tabs)
        vbox.append(content_box)

        # Status bar with Adwaita styling
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        status_box.add_css_class("toolbar")
        status_bar = Gtk.Label(label="Ready")
        status_bar.set_xalign(0)
        status_bar.set_margin_start(8)
        status_bar.set_margin_end(8)
        status_box.append(status_bar)
        vbox.append(status_box)


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
        
        # Connect TabView signals
        if self.tab_view:
            self.tab_view.connect("page-attached", self._on_page_attached)
            self.tab_view.connect("close-page", self._on_close_page)
            self.tab_view.connect("notify::selected-page", self._on_selected_page_changed)
        
        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()
        
        # Add any tabs that were created before the window
        for tab in self.browser.tabs:
            if tab not in self.tab_pages:
                self._add_tab_to_ui(tab)
        
        # Set the active tab in the UI
        if self.browser.active_tab and self.browser.active_tab in self.tab_pages:
            page = self.tab_pages[self.browser.active_tab]
            self.tab_view.set_selected_page(page)
        
        # Show the window
        self.window.present()
    
    def _add_tab_to_ui(self, tab):
        """Internal method to add a tab to the TabView UI."""
        # Create a simple placeholder for the tab
        # (Actual rendering happens in the shared drawing_area)
        placeholder = Gtk.Box()
        
        # Create the tab page
        page = self.tab_view.append(placeholder)
        page.set_title(tab.title)
        
        # Store mapping
        self.tab_pages[tab] = page
        
        # Select this tab
        self.tab_view.set_selected_page(page)
    
    def add_tab(self, tab):
        """Add a tab to the TabView."""
        if not self.tab_view:
            # Window not created yet, tab will be added when window is created
            return
        
        self._add_tab_to_ui(tab)
    
    def update_tab(self, tab):
        """Update tab title and other properties."""
        if tab in self.tab_pages:
            page = self.tab_pages[tab]
            page.set_title(tab.title)
    
    def remove_tab(self, tab):
        """Remove a tab from the TabView programmatically."""
        if tab not in self.tab_pages:
            return
        page = self.tab_pages[tab]
        del self.tab_pages[tab]
        # Directly close the page - this triggers _on_close_page but we've already removed from tab_pages
        self.tab_view.close_page(page)
    
    def set_active_tab(self, tab):
        """Set the active tab in the TabView."""
        if tab in self.tab_pages:
            page = self.tab_pages[tab]
            self.tab_view.set_selected_page(page)
    
    def _on_page_attached(self, tab_view, page, position):
        """Handle when a page is attached to the TabView."""
        self.logger.debug(f"Page attached at position {position}")
    
    def _on_close_page(self, tab_view, page):
        """Handle tab close request from UI.
        
        This is called when close_page() is invoked. We must call close_page_finish()
        to actually complete the page removal.
        """
        # Find the tab associated with this page
        tab_to_close = None
        for tab, tab_page in list(self.tab_pages.items()):
            if tab_page == page:
                tab_to_close = tab
                break
        
        if tab_to_close:
            # Remove from our tracking
            del self.tab_pages[tab_to_close]
            # Confirm the close - this actually removes the page from TabView
            self.tab_view.close_page_finish(page, True)
            # Call browser cleanup (but don't call remove_tab since we already handled it)
            self.browser.close_tab(tab_to_close)
            return True
        else:
            # Page not in our tracking - just confirm the close
            self.tab_view.close_page_finish(page, True)
            return True
    
    def _on_selected_page_changed(self, tab_view, pspec):
        """Handle tab selection change."""
        selected_page = tab_view.get_selected_page()
        if selected_page:
            # Find the tab associated with this page
            for tab, page in self.tab_pages.items():
                if page == selected_page:
                    self.browser.set_active_tab(tab)
                    break

    def _on_new_tab_clicked(self, btn: Gtk.Button):
        """Handle new tab button click."""
        self.browser.new_tab("about:startpage")

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

        # Render DOM content
        frame = self.browser.active_tab.main_frame if self.browser.active_tab else None
        document = frame.document if frame else None
        if document:
            self._render_dom_content(canvas, document, width, height)
        else:
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
    
    def _render_dom_content(self, canvas, document, width: int, height: int):
        """Render a basic DOM tree with headings, paragraphs, and lists."""
        from ..parser.html import Element, Text

        body = self._find_body(document)
        if not body:
            return

        blocks = self._collect_blocks(body)
        paint = skia.Paint()
        paint.setAntiAlias(True)
        paint.setColor(skia.ColorBLACK)

        x_margin = 20
        max_width = max(10, width - 2 * x_margin)
        y = 30

        for block in blocks:
            font_size = block.get("font_size", 14)
            font = skia.Font(skia.Typeface.MakeDefault(), font_size)
            text = block.get("text", "")
            if not text:
                y += font_size * 0.6
                continue

            # Optional bullet prefix
            if block.get("bullet"):
                text = f"• {text}"

            # Word wrapping per block
            words = text.split()
            lines = []
            current_line = []
            current_width = 0
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

            line_height = font_size * 1.4
            top_margin = block.get("margin_top", 6)
            y += top_margin
            for line in lines:
                if y > height - 20:
                    return
                canvas.drawString(line, x_margin, y, font, paint)
                y += line_height
            y += block.get("margin_bottom", 10)

    def _find_body(self, document):
        from ..parser.html import Element
        if isinstance(document, Element) and document.tag == "body":
            return document
        if hasattr(document, "children"):
            for child in document.children:
                if isinstance(child, Element) and child.tag == "body":
                    return child
                found = self._find_body(child)
                if found:
                    return found
        return None

    def _collect_blocks(self, node):
        """Flatten DOM into renderable blocks with basic styling."""
        from ..parser.html import Element, Text

        blocks = []

        def text_of(n):
            if isinstance(n, Text):
                return n.text
            if isinstance(n, Element):
                parts = []
                for c in n.children:
                    parts.append(text_of(c))
                return " ".join([p for p in parts if p]).strip()
            return ""

        for child in getattr(node, "children", []):
            if isinstance(child, Text):
                txt = child.text.strip()
                if txt:
                    blocks.append({"text": txt, "font_size": 14})
                continue

            if isinstance(child, Element):
                tag = child.tag.lower()
                content = text_of(child)
                if not content:
                    continue

                if tag == "h1":
                    blocks.append({"text": content, "font_size": 24, "margin_top": 12, "margin_bottom": 12})
                elif tag == "h2":
                    blocks.append({"text": content, "font_size": 20, "margin_top": 10, "margin_bottom": 10})
                elif tag == "h3":
                    blocks.append({"text": content, "font_size": 18, "margin_top": 8, "margin_bottom": 8})
                elif tag == "p":
                    blocks.append({"text": content, "font_size": 14, "margin_top": 6, "margin_bottom": 12})
                elif tag == "li":
                    blocks.append({"text": content, "font_size": 14, "bullet": True, "margin_top": 4, "margin_bottom": 4})
                elif tag in {"ul", "ol"}:
                    blocks.extend(self._collect_blocks(child))
                else:
                    # Generic element: render text
                    blocks.append({"text": content, "font_size": 14})

        return blocks

    def paint(self):
        """Trigger redraw of the drawing area."""
        if self.drawing_area:
            self.drawing_area.queue_draw()
    
    def _setup_keyboard_shortcuts(self):
        """Setup keyboard event handling for shortcuts."""
        if not self.window:
            return
        
        # Create event controller for key presses
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.window.add_controller(key_controller)
    
    def _on_key_pressed(self, controller, keyval, keycode, state):
        """Handle keyboard shortcuts."""
        # Check for Ctrl+Shift+D (DOM graph visualization)
        ctrl_pressed = state & Gdk.ModifierType.CONTROL_MASK
        shift_pressed = state & Gdk.ModifierType.SHIFT_MASK
        
        key_name = Gdk.keyval_name(keyval)
        
        if ctrl_pressed and shift_pressed and key_name in ('D', 'd'):
            self._show_dom_graph()
            return True  # Event handled
        
        return False  # Event not handled
    
    def _show_dom_graph(self):
        """Generate and display DOM graph for current tab."""
        from ..debug.dom_graph import render_dom_graph_to_svg, save_dom_graph, print_dom_tree
        import os
        from pathlib import Path
        
        if not self.browser.active_tab:
            self.logger.warning("No active tab to visualize")
            return
        
        frame = self.browser.active_tab.main_frame
        if not frame or not frame.document:
            self.logger.warning("No document to visualize")
            return
        
        # Generate output path
        output_dir = Path.home() / ".cache" / "bowser"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Try SVG first, fallback to DOT
        svg_path = output_dir / "dom_graph.svg"
        dot_path = output_dir / "dom_graph.dot"
        
        self.logger.info("Generating DOM graph...")
        
        # Print tree to console for debugging
        tree_text = print_dom_tree(frame.document, max_depth=15)
        print("\n" + "="*60)
        print("DOM TREE STRUCTURE:")
        print("="*60)
        print(tree_text)
        print("="*60 + "\n")
        
        # Try to render as SVG
        if render_dom_graph_to_svg(frame.document, str(svg_path)):
            # Open in new browser tab
            self.logger.info(f"Opening DOM graph in new tab: {svg_path}")
            self.browser.new_tab(f"about:dom-graph?path={svg_path}")
        else:
            # Fallback to DOT file
            if save_dom_graph(frame.document, str(dot_path)):
                self.logger.info(f"Opening DOM graph (DOT format) in new tab: {dot_path}")
                self.browser.new_tab(f"about:dom-graph?path={dot_path}")
    
    def _show_info_dialog(self, title: str, message: str):
        """Show an information dialog."""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.set_property("secondary-text", message)
        dialog.connect("response", lambda d, r: d.destroy())
        dialog.present()
