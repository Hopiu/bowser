## Plan: Bowser — Custom Web Browser from Scratch

Build a complete web browser following the [browser.engineering](https://browser.engineering/) curriculum, implementing all major components without relying on WebView wrappers.

---

### Language Choice

- Default: **Python** (matches browser.engineering; fastest to build). Use Skia (`skia-python`) + GTK (`PyGObject`).
- Optional ports: **Go** (networking/concurrency, single binary) or **Zig** (C interop, fine-grained control) once the Python version is feature-complete. Keep Python parity as the spec.

---

### GUI Toolkit: GTK via PyGObject

- Cross-platform; mature Python bindings.
- Paint with Skia (preferred) or Cairo; full control of pixels, no WebView wrappers.
- Alternative: Skia + SDL2/GLFW if you want lower-level window/input handling.

---

### Architecture Overview (from browser.engineering)

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                              │
│  ┌─────────┐  ┌─────────────────────────────────────────┐   │
│  │ Chrome  │  │                  Tab                    │   │
│  │ (GTK)   │  │  ┌───────┐  ┌────────┐  ┌───────────┐   │   │
│  │         │  │  │ Frame │  │ Frame  │  │  Frame    │   │   │
│  │ - tabs  │  │  │(main) │  │(iframe)│  │ (iframe)  │   │   │
│  │ - addr  │  │  └───────┘  └────────┘  └───────────┘   │   │
│  │ - back  │  └─────────────────────────────────────────┘   │
│  └─────────┘                                                │
└─────────────────────────────────────────────────────────────┘
```

---

### Implementation Phases

#### Part 1: Loading Pages
| Chapter | Component | Key Classes/Functions |
|---------|-----------|----------------------|
| 1 | URL & HTTP | `URL`, `request()`, `resolve()`, `COOKIE_JAR` |
| 2 | Drawing | `Browser`, `Chrome`, Skia/Cairo canvas |
| 3 | Text Formatting | `get_font()`, `linespace()`, word wrapping |

#### Part 2: Viewing Documents
| Chapter | Component | Key Classes/Functions |
|---------|-----------|----------------------|
| 4 | HTML Parsing | `HTMLParser`, `Text`, `Element`, `print_tree()` |
| 5 | Layout | `DocumentLayout`, `BlockLayout`, `LineLayout`, `TextLayout` |
| 6 | CSS | `CSSParser`, `TagSelector`, `DescendantSelector`, `style()` |
| 7 | Interaction | `Chrome`, hyperlinks, `click()`, `focus_element()` |

#### Part 3: Running Applications
| Chapter | Component | Key Classes/Functions |
|---------|-----------|----------------------|
| 8 | Forms | `submit_form()`, POST requests |
| 9 | JavaScript | `JSContext`, embed external engine (see below) |
| 10 | Security | Cookies, same-origin policy, XSS/CSRF protection |

#### Part 4: Modern Browsers
| Chapter | Component | Key Classes/Functions |
|---------|-----------|----------------------|
| 11 | Visual Effects | `Blend`, `Transform`, `CompositedLayer` |
| 12 | Threading | `Task`, `TaskRunner`, event loop |
| 13 | Animations | `NumericAnimation`, GPU compositing |
| 14 | Accessibility | `AccessibilityNode`, `speak_text()` |
| 15 | Embeds | `ImageLayout`, `IframeLayout`, `Frame` |
| 16 | Invalidation | `ProtectedField`, `dirty_style()`, incremental layout |

---

### JavaScript Engine Strategy

**Primary options (pick one to start):**
- **QuickJS / QuickJS-NG** — Small, fast, ES2020; approachable embedding.
- **Duktape** — Very small, forgiving; good starter.
- **LibJS** — Much larger; useful for reference, heavier to embed.

**Path:** start by embedding QuickJS (or QuickJS-NG). Add bindings for DOM APIs used in chapters. Optionally experiment with Duktape for simplicity. Custom interpreter later only for learning.

---

### Project Structure

```
bowser/
├── src/
│   ├── network/
│   │   ├── url.py          # URL parsing, resolution
│   │   ├── http.py         # HTTP/HTTPS requests
│   │   └── cookies.py      # Cookie jar management
│   ├── parser/
│   │   ├── html.py         # HTMLParser, Text, Element
│   │   └── css.py          # CSSParser, selectors
│   ├── layout/
│   │   ├── document.py     # DocumentLayout
│   │   ├── block.py        # BlockLayout, LineLayout
│   │   ├── inline.py       # TextLayout, InputLayout
│   │   └── embed.py        # ImageLayout, IframeLayout
│   ├── render/
│   │   ├── paint.py        # PaintCommand, Draw* classes
│   │   ├── composite.py    # CompositedLayer, visual effects
│   │   └── fonts.py        # Font management, text shaping
│   ├── script/
│   │   ├── context.py      # JSContext
│   │   ├── bindings.py     # DOM bindings for JS engine
│   │   └── runtime.js      # JS runtime helpers
│   ├── browser/
│   │   ├── tab.py          # Tab, Frame
│   │   ├── chrome.py       # Chrome (UI)
│   │   └── browser.py      # Main Browser class
│   └── accessibility/
│       └── a11y.py         # AccessibilityNode, screen reader
├── tests/
├── assets/
│   └── default.css         # User-agent stylesheet
└── main.py
```

---

### Development Milestones

- [ ] **M1**: Display "Hello World" in window (URL → HTTP → canvas)
- [ ] **M2**: Render plain HTML with text wrapping
- [ ] **M3**: Parse and apply basic CSS (colors, fonts, margins)
- [ ] **M4**: Clickable links and navigation
- [ ] **M5**: Form input and submission
- [ ] **M6**: JavaScript execution (console.log, DOM queries)
- [ ] **M7**: Event handling (onclick, onsubmit)
- [ ] **M8**: Images and iframes
- [ ] **M9**: Smooth scrolling and animations
- [ ] **M10**: Accessibility tree and keyboard navigation

---

### Key Dependencies (Python)

```
skia-python          # 2D graphics (or cairocffi)
PyGObject            # GTK bindings
pyduktape2           # JavaScript engine (or quickjs)
harfbuzz             # Text shaping (via uharfbuzz)
Pillow               # Image decoding
```

---

### Resources

- 📖 [browser.engineering](https://browser.engineering/) — Primary reference
- 📖 [Let's Build a Browser Engine](https://limpet.net/mbrubeck/2014/08/08/toy-layout-engine-1.html) — Matt Brubeck's Rust tutorial
- 🔧 [Skia Graphics Library](https://skia.org/)
- 🔧 [QuickJS](https://bellard.org/quickjs/) — Embeddable JS engine
