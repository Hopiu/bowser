# Bowser — Educational Web Browser

A custom web browser built from scratch following the [browser.engineering](https://browser.engineering/) curriculum.

**Status**: Early scaffolding phase (M0)

## Building

### Prerequisites
- Python 3.11+
- GTK 4 development libraries (Debian: `libgtk-4-dev libgtk-4-1`)
- Skia-Python (`skia-python`): `pip install skia-python`
- PyGObject (`PyGObject`): `pip install PyGObject`
- Graphviz (optional, for DOM visualization): `sudo apt install graphviz`

### Setup
```bash
uv sync
uv run bowser
```

## Usage

### Keyboard Shortcuts
- **Ctrl+Shift+D**: Generate and visualize DOM tree graph of current page
  - Opens visualization in a new browser tab
  - Displays interactive SVG graph (if Graphviz installed)
  - Falls back to DOT format if Graphviz not available
  - Prints tree structure to console

### Testing
Run the test suite:
```bash
# Install dev dependencies
uv sync --extra dev

# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage report
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_browser.py
```

### Development
```bash
# Format code
uv run black src tests

# Lint code
uv run ruff check src tests

# Type check
uv run mypy src
```

## Project Structure

```
bowser/
├── src/
│   ├── network/          # URL parsing, HTTP, cookies
│   ├── parser/           # HTML & CSS parsers
│   ├── layout/           # Block/inline/embedded layout
│   ├── render/           # Paint commands, fonts, compositing
│   ├── script/           # JavaScript integration
│   ├── browser/          # Tab/frame/chrome orchestration
│   └── accessibility/    # A11y tree and screen reader
├── assets/               # Stylesheets, images
├── tests/                # Unit tests
├── pyproject.toml        # Dependencies & build config
└── main.py               # Entry point
```

## Development Milestones

- [ ] **M0**: Project scaffold ✅
- [ ] **M1**: Display "Hello World" in GTK window with manual URL fetch & paint
- [ ] **M2**: Render plain HTML with text wrapping
- [ ] **M3**: Parse and apply basic CSS
- [ ] **M4**: Clickable links and navigation
- [ ] **M5**: Form input and submission
- [ ] **M6**: JavaScript execution (embed QuickJS)
- [ ] **M7**: Event handling
- [ ] **M8**: Images and iframes
- [ ] **M9**: Animations and visual effects
- [ ] **M10**: Accessibility and keyboard navigation

## References

- [Web Browser Engineering](https://browser.engineering/) — O'Reilly book
- [Let's Build a Browser Engine](https://limpet.net/mbrubeck/2014/08/08/toy-layout-engine-1.html) — Matt Brubeck's Rust tutorial
