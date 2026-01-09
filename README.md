# Bowser — Educational Web Browser

A custom web browser built from scratch following the [browser.engineering](https://browser.engineering/) curriculum.

**Status**: Early scaffolding phase (M0)

## Building

### Prerequisites
- Python 3.11+
- GTK 4 development libraries (Debian: `libgtk-4-dev libgtk-4-1`)
- Skia-Python (`skia-python`): `pip install skia-python`
- PyGObject (`PyGObject`): `pip install PyGObject`

### Setup
```bash
uv sync
uv run bowser
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
