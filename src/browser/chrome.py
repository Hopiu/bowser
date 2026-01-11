"""Browser chrome (Adwaita UI)."""

import gi
from typing import Optional
import logging
import cairo
import time
from pathlib import Path

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Gdk, Adw
import skia

# Import the render and layout packages
from ..render.fonts import get_font
from ..layout.document import DocumentLayout


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
        
        # Debug mode state
        self.debug_mode = False
        
        # FPS tracking for debug mode
        self.frame_times = []  # List of recent frame timestamps
        self.fps = 0.0
        
        # Profiling data
        self._last_profile = {}
        self._last_profile_total = 0.0
        
        # Scroll state
        self.scroll_y = 0
        self.document_height = 0  # Total document height for scroll limits
        self.viewport_height = 0  # Current viewport height
        
        # Scrollbar fade state
        self.scrollbar_opacity = 0.0
        self.scrollbar_fade_timeout = None
        
        # Selection state
        self.selection_start = None  # (x, y) of selection start
        self.selection_end = None    # (x, y) of selection end
        self.is_selecting = False    # True while mouse is dragging
        
        # Layout information for text selection
        # Each entry: {text, x, y, width, height, font_size, char_positions}
        # char_positions is a list of x offsets for each character
        self.text_layout = []
        
        # Layout cache to avoid recalculation on scroll
        self._layout_cache_width = 0
        self._layout_cache_doc_id = None
        self._layout_rects = []   # Cached debug rects
        
        # Paint cache
        self._text_paint = None
        
        # Sub-timings for detailed profiling
        self._render_sub_timings = {}
        self._visible_line_count = 0

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
        self.drawing_area.set_can_focus(True)  # Allow focus for keyboard events
        self.drawing_area.set_focusable(True)
        content_box.append(self.drawing_area)
        
        # Add scroll controller for mouse wheel
        scroll_controller = Gtk.EventControllerScroll.new(
            Gtk.EventControllerScrollFlags.VERTICAL
        )
        scroll_controller.connect("scroll", self._on_scroll)
        self.drawing_area.add_controller(scroll_controller)
        
        # Add mouse button controller for selection
        click_controller = Gtk.GestureClick.new()
        click_controller.connect("pressed", self._on_mouse_pressed)
        click_controller.connect("released", self._on_mouse_released)
        self.drawing_area.add_controller(click_controller)
        
        # Add motion controller for drag selection
        motion_controller = Gtk.EventControllerMotion.new()
        motion_controller.connect("motion", self._on_mouse_motion)
        self.drawing_area.add_controller(motion_controller)
        
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
        # Track frame time for FPS calculation
        current_time = time.time()
        self.frame_times.append(current_time)
        # Keep only last 60 frame times (about 1 second at 60fps)
        self.frame_times = [t for t in self.frame_times if current_time - t < 1.0]
        if len(self.frame_times) > 1:
            self.fps = len(self.frame_times)
        
        # Profiling timers
        profile_start = time.perf_counter()
        timings = {}
        
        # Create Skia surface for this frame
        t0 = time.perf_counter()
        self.skia_surface = skia.Surface(width, height)
        canvas = self.skia_surface.getCanvas()
        timings['surface_create'] = time.perf_counter() - t0
        
        # Store viewport height
        self.viewport_height = height

        # White background
        t0 = time.perf_counter()
        canvas.clear(skia.ColorWHITE)
        timings['clear'] = time.perf_counter() - t0

        # Render DOM content
        frame = self.browser.active_tab.main_frame if self.browser.active_tab else None
        document = frame.document if frame else None
        if document:
            t0 = time.perf_counter()
            self._render_dom_content(canvas, document, width, height)
            timings['render_dom'] = time.perf_counter() - t0
            
            t0 = time.perf_counter()
            self._draw_scrollbar(canvas, width, height)
            timings['scrollbar'] = time.perf_counter() - t0
            
            if self.debug_mode:
                self._draw_fps_counter(canvas, width)
        else:
            paint = skia.Paint()
            paint.setAntiAlias(True)
            paint.setColor(skia.ColorBLACK)
            font = self._get_font(20)
            canvas.drawString("Bowser — Enter a URL to browse", 20, 50, font, paint)

        # Get raw pixel data from Skia surface
        t0 = time.perf_counter()
        image = self.skia_surface.makeImageSnapshot()
        timings['snapshot'] = time.perf_counter() - t0
        
        t0 = time.perf_counter()
        pixels = image.tobytes()
        timings['tobytes'] = time.perf_counter() - t0
        
        # Create Cairo ImageSurface from raw pixels
        t0 = time.perf_counter()
        cairo_surface = cairo.ImageSurface.create_for_data(
            bytearray(pixels),
            cairo.FORMAT_ARGB32,
            width,
            height,
            width * 4  # stride
        )
        timings['cairo_surface'] = time.perf_counter() - t0
        
        # Blit Cairo surface to context
        t0 = time.perf_counter()
        context.set_source_surface(cairo_surface, 0, 0)
        context.paint()
        timings['cairo_blit'] = time.perf_counter() - t0
        
        total_time = time.perf_counter() - profile_start
        
        # Store profiling data for debug display
        if self.debug_mode:
            self._last_profile = timings
            self._last_profile_total = total_time
    
    def _render_dom_content(self, canvas, document, width: int, height: int):
        """Render a basic DOM tree with headings, paragraphs, and lists."""

        sub_timings = {}
        
        # Check if we need to rebuild layout cache
        t0 = time.perf_counter()
        doc_id = id(document)
        needs_rebuild = (
            self._layout_cache_doc_id != doc_id or
            self._layout_cache_width != width or
            not self.text_layout
        )
        
        if needs_rebuild:
            self._rebuild_layout(document, width)
            self._layout_cache_doc_id = doc_id
            self._layout_cache_width = width
            self.logger.debug(f"Layout rebuilt: {len(self.text_layout)} lines")
        sub_timings['layout_check'] = time.perf_counter() - t0
        
        if not self.text_layout:
            return
        
        # Apply scroll offset
        t0 = time.perf_counter()
        canvas.save()
        canvas.translate(0, -self.scroll_y)
        sub_timings['transform'] = time.perf_counter() - t0
        
        # Get or create cached paint
        if self._text_paint is None:
            self._text_paint = skia.Paint()
            self._text_paint.setAntiAlias(True)
            self._text_paint.setColor(skia.ColorBLACK)
        
        # Only draw visible lines
        t0 = time.perf_counter()
        visible_top = self.scroll_y - 50
        visible_bottom = self.scroll_y + height + 50
        
        visible_count = 0
        for line_info in self.text_layout:
            line_y = line_info["y"] + line_info["font_size"]  # Baseline y
            if line_y < visible_top or line_y - line_info["height"] > visible_bottom:
                continue
            
            visible_count += 1
            font = self._get_font(line_info["font_size"])
            canvas.drawString(line_info["text"], line_info["x"], line_y, font, self._text_paint)
        sub_timings['draw_text'] = time.perf_counter() - t0
        
        # Draw selection highlight
        t0 = time.perf_counter()
        if self.selection_start and self.selection_end:
            self._draw_text_selection(canvas)
        sub_timings['selection'] = time.perf_counter() - t0
        
        # Draw debug overlays
        t0 = time.perf_counter()
        if self.debug_mode:
            self._draw_debug_overlays(canvas, self._layout_rects, document)
        sub_timings['debug_overlay'] = time.perf_counter() - t0
        
        t0 = time.perf_counter()
        canvas.restore()
        sub_timings['restore'] = time.perf_counter() - t0
        
        # Store sub-timings for display
        if self.debug_mode:
            self._render_sub_timings = sub_timings
            self._visible_line_count = visible_count
    
    def _get_font(self, size: int):
        """Get a cached font for the given size."""
        return get_font(size)
    
    def _rebuild_layout(self, body, width: int):
        """Rebuild the layout cache for text positioning using DocumentLayout."""
        self.text_layout = []
        self._layout_rects = []
        
        # Use the new DocumentLayout for layout calculation
        doc_layout = DocumentLayout(body)
        layout_lines = doc_layout.layout(width)
        
        # Convert LayoutLine objects to text_layout format
        x_margin = 20
        max_width = max(10, width - 2 * x_margin)
        
        for line in layout_lines:
            self.text_layout.append({
                "text": line.text,
                "x": line.x,
                "y": line.y,  # Top of line
                "width": line.width,
                "height": line.height,
                "font_size": line.font_size,
                "char_positions": line.char_positions
            })
        
        # Build layout rects for debug mode from blocks
        for block in doc_layout.blocks:
            self._layout_rects.append({
                "x": block.x - 5,
                "y": block.y - block.lines[0].font_size if block.lines else block.y,
                "width": block.width + 10,
                "height": block.height + 5,
                "type": block.block_type
            })
        
        # Store total document height
        self.document_height = doc_layout.height

    def _draw_selection_highlight(self, canvas, width: int):
        """Draw selection highlight rectangle."""
        if not self.selection_start or not self.selection_end:
            return
        
        x1, y1 = self.selection_start
        x2, y2 = self.selection_end
        
        # Normalize coordinates
        left = min(x1, x2)
        right = max(x1, x2)
        top = min(y1, y2)
        bottom = max(y1, y2)
        
        paint = skia.Paint()
        paint.setColor(skia.Color(100, 149, 237, 80))  # Cornflower blue, semi-transparent
        paint.setStyle(skia.Paint.kFill_Style)
        
        rect = skia.Rect.MakeLTRB(left, top, right, bottom)
        canvas.drawRect(rect, paint)
    
    def _draw_debug_overlays(self, canvas, layout_rects: list, document):
        """Draw debug overlays showing element boxes."""
        # Color scheme for different element types
        colors = {
            "block": skia.Color(255, 0, 0, 60),      # Red - block elements
            "inline": skia.Color(0, 0, 255, 60),     # Blue - inline elements
            "list-item": skia.Color(0, 255, 0, 60), # Green - list items
            "text": skia.Color(255, 255, 0, 60),    # Yellow - text nodes
        }
        
        border_colors = {
            "block": skia.Color(255, 0, 0, 180),
            "inline": skia.Color(0, 0, 255, 180),
            "list-item": skia.Color(0, 255, 0, 180),
            "text": skia.Color(255, 255, 0, 180),
        }
        
        for rect_info in layout_rects:
            block_type = rect_info.get("type", "block")
            
            # Fill
            fill_paint = skia.Paint()
            fill_paint.setColor(colors.get(block_type, colors["block"]))
            fill_paint.setStyle(skia.Paint.kFill_Style)
            
            rect = skia.Rect.MakeLTRB(
                rect_info["x"],
                rect_info["y"],
                rect_info["x"] + rect_info["width"],
                rect_info["y"] + rect_info["height"]
            )
            canvas.drawRect(rect, fill_paint)
            
            # Border
            border_paint = skia.Paint()
            border_paint.setColor(border_colors.get(block_type, border_colors["block"]))
            border_paint.setStyle(skia.Paint.kStroke_Style)
            border_paint.setStrokeWidth(1)
            canvas.drawRect(rect, border_paint)
        
        # Draw legend in top-right corner
        self._draw_debug_legend(canvas)
    
    def _draw_debug_legend(self, canvas):
        """Draw debug mode legend."""
        # Position in screen coordinates (add scroll offset back)
        legend_x = 10
        legend_y = self.scroll_y + 10
        
        font = self._get_font(11)
        
        # Background
        bg_paint = skia.Paint()
        bg_paint.setColor(skia.Color(0, 0, 0, 200))
        bg_paint.setStyle(skia.Paint.kFill_Style)
        canvas.drawRect(skia.Rect.MakeLTRB(legend_x, legend_y, legend_x + 150, legend_y + 85), bg_paint)
        
        text_paint = skia.Paint()
        text_paint.setColor(skia.ColorWHITE)
        text_paint.setAntiAlias(True)
        
        canvas.drawString("DEBUG MODE (Ctrl+Shift+O)", legend_x + 5, legend_y + 15, font, text_paint)
        
        items = [
            ("Red", "Block elements", skia.Color(255, 100, 100, 255)),
            ("Blue", "Inline elements", skia.Color(100, 100, 255, 255)),
            ("Green", "List items", skia.Color(100, 255, 100, 255)),
        ]
        
        y_offset = 30
        for label, desc, color in items:
            color_paint = skia.Paint()
            color_paint.setColor(color)
            canvas.drawRect(skia.Rect.MakeLTRB(legend_x + 5, legend_y + y_offset, legend_x + 15, legend_y + y_offset + 10), color_paint)
            canvas.drawString(f"{label}: {desc}", legend_x + 20, legend_y + y_offset + 10, font, text_paint)
            y_offset += 18
    
    def _draw_fps_counter(self, canvas, width: int):
        """Draw FPS counter and profiling info in top-right corner."""
        font = self._get_font(11)
        small_font = self._get_font(9)
        
        # Calculate panel size based on profile data
        panel_width = 200
        num_profile_lines = len(self._last_profile) + 2  # +2 for FPS and total
        num_sub_lines = len(self._render_sub_timings) + 1 if self._render_sub_timings else 0
        panel_height = 18 + num_profile_lines * 12 + num_sub_lines * 11 + 10
        
        # Position in top-right
        panel_x = width - panel_width - 10
        panel_y = 10
        
        # Background
        bg_paint = skia.Paint()
        bg_paint.setColor(skia.Color(0, 0, 0, 200))
        bg_paint.setStyle(skia.Paint.kFill_Style)
        canvas.drawRect(skia.Rect.MakeLTRB(
            panel_x, panel_y, 
            panel_x + panel_width, panel_y + panel_height
        ), bg_paint)
        
        text_paint = skia.Paint()
        text_paint.setAntiAlias(True)
        
        # FPS with color
        if self.fps >= 50:
            text_paint.setColor(skia.Color(100, 255, 100, 255))
        elif self.fps >= 30:
            text_paint.setColor(skia.Color(255, 255, 100, 255))
        else:
            text_paint.setColor(skia.Color(255, 100, 100, 255))
        
        y = panel_y + 14
        canvas.drawString(f"FPS: {self.fps:.0f}", panel_x + 5, y, font, text_paint)
        
        # Total frame time
        text_paint.setColor(skia.ColorWHITE)
        total_ms = self._last_profile_total * 1000
        y += 14
        canvas.drawString(f"Frame: {total_ms:.1f}ms", panel_x + 5, y, font, text_paint)
        
        # Profile breakdown
        gray_paint = skia.Paint()
        gray_paint.setAntiAlias(True)
        gray_paint.setColor(skia.Color(180, 180, 180, 255))
        
        if self._last_profile:
            # Sort by time descending
            sorted_items = sorted(
                self._last_profile.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            for name, duration in sorted_items:
                y += 12
                ms = duration * 1000
                pct = (duration / self._last_profile_total * 100) if self._last_profile_total > 0 else 0
                # Color code: red if >50% of frame time
                if pct > 50:
                    gray_paint.setColor(skia.Color(255, 150, 150, 255))
                elif pct > 25:
                    gray_paint.setColor(skia.Color(255, 220, 150, 255))
                else:
                    gray_paint.setColor(skia.Color(180, 180, 180, 255))
                canvas.drawString(f"{name}: {ms:.1f}ms ({pct:.0f}%)", panel_x + 8, y, small_font, gray_paint)
        
        # Show render_dom sub-timings if available
        if self._render_sub_timings:
            y += 16
            text_paint.setColor(skia.Color(150, 200, 255, 255))
            canvas.drawString(f"render_dom breakdown ({self._visible_line_count} lines):", panel_x + 5, y, small_font, text_paint)
            
            sub_sorted = sorted(self._render_sub_timings.items(), key=lambda x: x[1], reverse=True)
            for name, duration in sub_sorted:
                y += 11
                ms = duration * 1000
                gray_paint.setColor(skia.Color(150, 180, 200, 255))
                canvas.drawString(f"  {name}: {ms:.2f}ms", panel_x + 8, y, small_font, gray_paint)

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
        
        # Ctrl+Shift+D: DOM graph visualization
        if ctrl_pressed and shift_pressed and key_name in ('D', 'd'):
            self._show_dom_graph()
            return True
        
        # Ctrl+Shift+O: Toggle debug mode (DOM outline visualization)
        if ctrl_pressed and shift_pressed and key_name in ('O', 'o'):
            self._toggle_debug_mode()
            return True
        
        # Page scrolling with arrow keys, Page Up/Down, Home/End
        scroll_amount = 50
        if key_name == 'Down':
            self._scroll_by(scroll_amount)
            return True
        elif key_name == 'Up':
            self._scroll_by(-scroll_amount)
            return True
        elif key_name == 'Page_Down':
            self._scroll_by(400)
            return True
        elif key_name == 'Page_Up':
            self._scroll_by(-400)
            return True
        elif key_name == 'Home' and ctrl_pressed:
            self.scroll_y = 0
            self.paint()
            return True
        elif key_name == 'End' and ctrl_pressed:
            self.scroll_y = 10000  # Will be clamped
            self.paint()
            return True
        elif key_name == 'space':
            # Space scrolls down, Shift+Space scrolls up
            if shift_pressed:
                self._scroll_by(-400)
            else:
                self._scroll_by(400)
            return True
        
        return False  # Event not handled
    
    def _toggle_debug_mode(self):
        """Toggle debug mode for DOM visualization."""
        self.debug_mode = not self.debug_mode
        mode_str = "ON" if self.debug_mode else "OFF"
        self.logger.info(f"Debug mode: {mode_str}")
        self.paint()
    
    def _scroll_by(self, delta: int):
        """Scroll the page by the given amount, clamped to document bounds."""
        max_scroll = max(0, self.document_height - self.viewport_height)
        self.scroll_y = max(0, min(max_scroll, self.scroll_y + delta))
        self._show_scrollbar()
        self.paint()
    
    def _show_scrollbar(self):
        """Show scrollbar and schedule fade out."""
        from gi.repository import GLib
        
        self.scrollbar_opacity = 1.0
        
        # Cancel any existing fade timeout
        if self.scrollbar_fade_timeout:
            GLib.source_remove(self.scrollbar_fade_timeout)
        
        # Schedule fade out after 1 second
        self.scrollbar_fade_timeout = GLib.timeout_add(1000, self._fade_scrollbar)
    
    def _fade_scrollbar(self):
        """Gradually fade out the scrollbar."""
        from gi.repository import GLib
        
        self.scrollbar_opacity -= 0.1
        if self.scrollbar_opacity <= 0:
            self.scrollbar_opacity = 0
            self.scrollbar_fade_timeout = None
            self.paint()
            return False  # Stop the timeout
        
        self.paint()
        # Continue fading
        self.scrollbar_fade_timeout = GLib.timeout_add(50, self._fade_scrollbar)
        return False  # This instance is done
    
    def _draw_scrollbar(self, canvas, width: int, height: int):
        """Draw the scrollbar overlay."""
        if self.scrollbar_opacity <= 0 or self.document_height <= height:
            return
        
        # Calculate scrollbar dimensions
        scrollbar_width = 8
        scrollbar_margin = 4
        scrollbar_x = width - scrollbar_width - scrollbar_margin
        
        # Track height (full viewport)
        track_height = height - 2 * scrollbar_margin
        
        # Thumb size proportional to viewport/document ratio
        thumb_ratio = height / self.document_height
        thumb_height = max(30, track_height * thumb_ratio)
        
        # Thumb position based on scroll position
        max_scroll = max(1, self.document_height - height)
        scroll_ratio = self.scroll_y / max_scroll
        thumb_y = scrollbar_margin + scroll_ratio * (track_height - thumb_height)
        
        # Draw track (subtle)
        alpha = int(30 * self.scrollbar_opacity)
        track_paint = skia.Paint()
        track_paint.setColor(skia.Color(0, 0, 0, alpha))
        track_paint.setStyle(skia.Paint.kFill_Style)
        track_rect = skia.RRect.MakeRectXY(
            skia.Rect.MakeLTRB(scrollbar_x, scrollbar_margin, 
                              scrollbar_x + scrollbar_width, height - scrollbar_margin),
            scrollbar_width / 2, scrollbar_width / 2
        )
        canvas.drawRRect(track_rect, track_paint)
        
        # Draw thumb
        alpha = int(150 * self.scrollbar_opacity)
        thumb_paint = skia.Paint()
        thumb_paint.setColor(skia.Color(100, 100, 100, alpha))
        thumb_paint.setStyle(skia.Paint.kFill_Style)
        thumb_rect = skia.RRect.MakeRectXY(
            skia.Rect.MakeLTRB(scrollbar_x, thumb_y,
                              scrollbar_x + scrollbar_width, thumb_y + thumb_height),
            scrollbar_width / 2, scrollbar_width / 2
        )
        canvas.drawRRect(thumb_rect, thumb_paint)
    
    def _on_scroll(self, controller, dx, dy):
        """Handle mouse wheel scroll."""
        scroll_amount = int(dy * 50)  # Scale scroll amount
        self._scroll_by(scroll_amount)
        return True
    
    def _on_mouse_pressed(self, gesture, n_press, x, y):
        """Handle mouse button press for text selection."""
        self.selection_start = (x, y + self.scroll_y)
        self.selection_end = None
        self.is_selecting = True
        self.drawing_area.grab_focus()
    
    def _on_mouse_released(self, gesture, n_press, x, y):
        """Handle mouse button release for text selection."""
        if self.is_selecting:
            self.selection_end = (x, y + self.scroll_y)
            self.is_selecting = False
            # Extract selected text
            selected_text = self._get_selected_text()
            if selected_text:
                self.logger.info(f"Selected text: {selected_text[:100]}...")
                # Copy to clipboard
                self._copy_to_clipboard(selected_text)
            self.paint()
    
    def _on_mouse_motion(self, controller, x, y):
        """Handle mouse motion for drag selection."""
        if self.is_selecting:
            self.selection_end = (x, y + self.scroll_y)
            self.paint()
    
    def _draw_text_selection(self, canvas):
        """Draw selection highlight for selected text at character level."""
        if not self.selection_start or not self.selection_end:
            return
        
        # Normalize selection: start should be before end in reading order
        if (self.selection_start[1] > self.selection_end[1] or
            (self.selection_start[1] == self.selection_end[1] and 
             self.selection_start[0] > self.selection_end[0])):
            sel_start = self.selection_end
            sel_end = self.selection_start
        else:
            sel_start = self.selection_start
            sel_end = self.selection_end
        
        paint = skia.Paint()
        paint.setColor(skia.Color(100, 149, 237, 100))  # Cornflower blue
        paint.setStyle(skia.Paint.kFill_Style)
        
        for line_info in self.text_layout:
            line_top = line_info["y"]
            line_bottom = line_info["y"] + line_info["height"]
            line_left = line_info["x"]
            char_positions = line_info.get("char_positions", [])
            text = line_info["text"]
            
            # Skip lines completely outside selection
            if line_bottom < sel_start[1] or line_top > sel_end[1]:
                continue
            
            # Determine selection bounds for this line
            hl_left = line_left
            hl_right = line_left + line_info["width"]
            
            # If this line contains the start of selection
            if line_top <= sel_start[1] < line_bottom:
                # Find character index at sel_start x
                start_char_idx = self._x_to_char_index(sel_start[0], line_left, char_positions)
                hl_left = line_left + char_positions[start_char_idx] if start_char_idx < len(char_positions) else line_left
            
            # If this line contains the end of selection
            if line_top <= sel_end[1] < line_bottom:
                # Find character index at sel_end x
                end_char_idx = self._x_to_char_index(sel_end[0], line_left, char_positions)
                hl_right = line_left + char_positions[end_char_idx] if end_char_idx < len(char_positions) else hl_right
            
            # Draw highlight
            if hl_right > hl_left:
                rect = skia.Rect.MakeLTRB(hl_left, line_top, hl_right, line_bottom)
                canvas.drawRect(rect, paint)
    
    def _x_to_char_index(self, x: float, line_x: float, char_positions: list) -> int:
        """Convert x coordinate to character index within a line."""
        rel_x = x - line_x
        if rel_x <= 0:
            return 0
        
        # Binary search for the character position
        for i, pos in enumerate(char_positions):
            if pos >= rel_x:
                # Check if closer to this char or previous
                if i > 0 and (pos - rel_x) > (rel_x - char_positions[i-1]):
                    return i - 1
                return i
        
        return len(char_positions) - 1
    
    def _get_selected_text(self) -> str:
        """Extract text from the current selection at character level."""
        if not self.selection_start or not self.selection_end or not self.text_layout:
            return ""
        
        # Normalize selection: start should be before end in reading order
        if (self.selection_start[1] > self.selection_end[1] or
            (self.selection_start[1] == self.selection_end[1] and 
             self.selection_start[0] > self.selection_end[0])):
            sel_start = self.selection_end
            sel_end = self.selection_start
        else:
            sel_start = self.selection_start
            sel_end = self.selection_end
        
        selected_parts = []
        
        for line_info in self.text_layout:
            line_top = line_info["y"]
            line_bottom = line_info["y"] + line_info["height"]
            line_left = line_info["x"]
            char_positions = line_info.get("char_positions", [])
            text = line_info["text"]
            
            # Skip lines completely outside selection
            if line_bottom < sel_start[1] or line_top > sel_end[1]:
                continue
            
            start_idx = 0
            end_idx = len(text)
            
            # If this line contains the start of selection
            if line_top <= sel_start[1] < line_bottom:
                start_idx = self._x_to_char_index(sel_start[0], line_left, char_positions)
            
            # If this line contains the end of selection
            if line_top <= sel_end[1] < line_bottom:
                end_idx = self._x_to_char_index(sel_end[0], line_left, char_positions)
            
            # Extract the selected portion
            if end_idx > start_idx:
                selected_parts.append(text[start_idx:end_idx])
        
        return " ".join(selected_parts)
    
    def _copy_to_clipboard(self, text: str):
        """Copy text to system clipboard."""
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.set(text)
    
    def _show_dom_graph(self):
        """Generate and display DOM graph for current tab."""
        from ..debug.dom_graph import render_dom_graph_to_svg, save_dom_graph, print_dom_tree
        
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
