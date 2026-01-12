# Bowser — Educational Web Browser

A custom web browser built from scratch following the [browser.engineering](https://browser.engineering/) curriculum. Features a clean architecture with Skia-based rendering, GTK 4/Adwaita UI, and proper separation of concerns.

**Status**: Milestone 3 - Basic HTML rendering with text layout and image support

## Features

- **Adwaita Tab Bar** - Modern GNOME-style tab management
- **Skia Rendering** - Hardware-accelerated 2D graphics
- **Text Layout** - Word wrapping, character-level selection
- **Image Support** - Load and render images from HTTP, data URLs, and local files
- **DOM Parsing** - HTML parsing with proper tree structure
- **Debug Mode** - Visual layout debugging with FPS counter
- **DOM Visualization** - Generate visual graphs of page structure

## Quick Start

```bash
# Install dependencies and run
uv sync
uv run bowser

# Browse a website
uv run bowser example.com

# Enable debug mode (shows FPS, layout boxes)
uv run bowser example.com --debug
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+T` | New tab |
| `Ctrl+W` | Close tab |
| `Ctrl+L` | Focus address bar |
| `Ctrl+Shift+D` | Generate DOM visualization |
| `Ctrl+Shift+O` | Toggle debug mode |

## Architecture

```
bowser/
├── src/
│   ├── browser/           # Browser UI (chrome.py, tab.py)
│   │   ├── browser.py     # Application orchestration
│   │   ├── chrome.py      # GTK/Adwaita window, tab bar, address bar
│   │   └── tab.py         # Tab and frame management
│   │
│   ├── parser/            # Document parsing
│   │   ├── html.py        # HTML → DOM tree (Element, Text nodes)
│   │   └── css.py         # CSS parsing (stub)
│   │
│   ├── layout/            # Layout calculation
│   │   ├── document.py    # DocumentLayout - full page layout
│   │   ├── block.py       # BlockLayout, LineLayout - block elements
│   │   ├── inline.py      # TextLayout, InlineLayout - text runs
│   │   └── embed.py       # ImageLayout - embedded content
│   │
│   ├── render/            # Painting & rendering
│   │   ├── pipeline.py    # RenderPipeline - coordinates layout/paint
│   │   ├── fonts.py       # FontCache - Skia font management
│   │   ├── paint.py       # DisplayList, DrawText, DrawRect, DrawImage
│   │   └── composite.py   # Layer compositing
│   │
│   ├── network/           # Networking
│   │   ├── http.py        # HTTP client with redirects
│   │   ├── url.py         # URL parsing and normalization
│   │   ├── cookies.py     # Cookie management
│   │   ├── images.py      # Image loading and caching
│   │   └── tasks.py       # Async task queue for background loading
│   │
│   ├── debug/             # Development tools
│   │   └── dom_graph.py   # DOM tree visualization
│   │
│   └── templates.py       # Page templates (start page, errors)
│
├── tests/                 # Test suite
└── main.py                # Entry point
```

### Design Principles

**Separation of Concerns:**
- `parser/` - Pure DOM data structures (Element, Text)
- `layout/` - Position and size calculations (x, y, width, height)
- `render/` - Drawing commands and font management
- `browser/` - UI only (tabs, address bar, event handling)

**Key Classes:**

| Class | Package | Responsibility |
|-------|---------|----------------|
| `Element`, `Text` | parser | DOM tree nodes |
| `DocumentLayout` | layout | Page layout with line positioning |
| `LayoutLine`, `LayoutBlock` | layout | Positioned text with bounding boxes |
| `ImageLayout`, `LayoutImage` | layout | Image sizing and positioning |
| `RenderPipeline` | render | Coordinates layout → paint |
| `DrawImage` | render | Image rendering command |
| `FontCache` | render | Skia font caching |
| `ImageCache` | network | Image loading and caching |
| `Chrome` | browser | GTK window, delegates to RenderPipeline |

## Development

### Prerequisites

- Python 3.11+
- GTK 4 (`libgtk-4-dev libgtk-4-1`)
- libadwaita (`libadwaita-1-dev`)
- Graphviz (optional, for DOM visualization)

```bash
# Debian/Ubuntu
sudo apt install libgtk-4-dev libadwaita-1-dev graphviz
```

### Testing

```bash
uv run pytest              # Run all tests
uv run pytest -v           # Verbose output
uv run pytest --cov=src    # Coverage report
```

### Code Quality

```bash
uv run black src tests     # Format code
uv run ruff check src      # Lint
uv run mypy src            # Type check
```

## Debug Mode

Enable with `--debug` flag or press `Ctrl+Shift+O` at runtime.

Shows:
- **FPS counter** with frame timing breakdown
- **Layout boxes** colored by element type:
  - Red: Block elements (`<div>`, `<p>`)
  - Blue: Inline elements (`<span>`, `<a>`)
  - Green: List items (`<li>`)

## Milestones

- [x] **M0**: Project scaffold
- [x] **M1**: GTK window with Skia rendering
- [x] **M2**: HTML parsing and text layout
- [x] **M3**: Image loading and rendering
- [ ] **M4**: CSS parsing and styling
- [ ] **M5**: Clickable links and navigation
- [ ] **M6**: Form input and submission
- [ ] **M7**: JavaScript execution
- [ ] **M8**: Event handling

## Image Support

Bowser supports loading and rendering images from multiple sources:

### Supported Sources

- **HTTP/HTTPS URLs**: `<img src="https://example.com/image.png">`
- **Data URLs**: `<img src="data:image/png;base64,...">`
- **Local files**: `<img src="file:///path/to/image.png">`

### Features

- **Async loading**: Images load in background threads, keeping UI responsive
- **Smart sizing**: Respects width/height attributes, maintains aspect ratios
- **Caching**: Thread-safe global image cache prevents redundant loads
- **Alt text placeholders**: Shows placeholder with alt text when images fail
- **Format support**: PNG, JPEG, GIF, WebP, and more (via Skia)
- **Viewport culling**: Only renders visible images for performance
- **Progressive display**: Page shows immediately, images appear as they load

### Example

```html
<!-- Basic image -->
<img src="photo.jpg">

<!-- Sized image with aspect ratio -->
<img src="photo.jpg" width="300">

<!-- With alt text for accessibility -->
<img src="photo.jpg" alt="A beautiful sunset">

<!-- Data URL (embedded image) -->
<img src="data:image/png;base64,iVBORw0KG...">
```

### Architecture

```
HTML <img> tag
    ↓
ImageLayout.load(async=True)
    ↓
TaskQueue (background thread pool)
    ↓
load_image() → HTTP/file/data URL
    ↓                    ↓
ImageCache          GLib.idle_add
(thread-safe)            ↓
                   on_complete callback
                         ↓
                   ImageLayout.image = loaded
                         ↓
                   RenderPipeline._request_redraw()
                         ↓
                   DrawImage.execute() → Canvas
```

## References

- [Web Browser Engineering](https://browser.engineering/) — O'Reilly book
- [Let's Build a Browser Engine](https://limpet.net/mbrubeck/2014/08/08/toy-layout-engine-1.html) — Matt Brubeck

## License

MIT
