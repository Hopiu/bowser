# DOM Visualization Feature - Implementation Summary

## Overview
Added a keyboard shortcut (Ctrl+Shift+D) to generate and visualize the DOM tree of the current tab as a graph.

## Files Created

### Core Implementation
- **src/debug/__init__.py** - Debug utilities package
- **src/debug/dom_graph.py** - DOM graph generation and visualization
  - `generate_dot_graph()` - Generates Graphviz DOT format
  - `save_dom_graph()` - Saves DOT file
  - `render_dom_graph_to_svg()` - Renders to SVG (requires graphviz)
  - `print_dom_tree()` - Text tree representation

### Tests
- **tests/test_dom_graph.py** - Comprehensive test suite (10 tests, all passing)
  - Tests graph generation, coloring, escaping, truncation
  - Tests tree printing with proper indentation
  - Tests depth limiting and attribute handling

### Documentation
- **docs/DOM_VISUALIZATION.md** - Feature documentation
- **test_dom.html** - Example test page
- Updated **README.md** with keyboard shortcuts section

## Implementation Details

### Browser Integration (src/browser/chrome.py)

1. **Keyboard Shortcut Setup**
   - Added `_setup_keyboard_shortcuts()` method
   - Registers GTK EventControllerKey for key presses
   - Listens for Ctrl+Shift+D combination

2. **DOM Graph Handler**
   - Added `_on_key_pressed()` callback
   - Added `_show_dom_graph()` method that:
     - Gets current tab's DOM document
     - Generates graph in DOT format
     - Attempts SVG rendering (if graphviz installed)
     - Falls back to DOT file
     - Prints tree to console
     - Shows info dialog with result

3. **UI Feedback**
   - Added `_show_info_dialog()` for user notifications
   - Opens generated SVG automatically with xdg-open

### Graph Features

**Color Coding:**
- Light green: `<html>`, `<body>`
- Light yellow: Headings (`<h1>`-`<h6>`)
- Light gray: Block elements (`<div>`, `<p>`, `<span>`)
- Light cyan: Lists (`<ul>`, `<ol>`, `<li>`)
- Light pink: Interactive (`<a>`, `<button>`)
- Light blue: Text nodes
- White: Other elements

**Node Information:**
- Element nodes show tag name and up to 3 attributes
- Text nodes show content preview (max 50 chars)
- Hierarchical edges show parent-child relationships

**Output:**
- Files saved to `~/.cache/bowser/`
- `dom_graph.svg` - Visual graph (if graphviz available)
- `dom_graph.dot` - DOT format definition
- Console output shows full tree structure

## Usage

1. Open any page in Bowser
2. Press **Ctrl+Shift+D**
3. View results:
   - Console: Text tree structure
   - File browser: Opens SVG (if graphviz installed)
   - Dialog: Shows file location

## Testing

All tests passing:
```bash
uv run pytest tests/test_dom_graph.py -v
# 10 passed in 0.11s
```

Test coverage:
- Empty document handling
- Simple HTML structures
- Nested elements
- Attributes rendering
- Text escaping
- Long text truncation
- Color coding
- Tree indentation
- Depth limiting

## Dependencies

**Required:**
- Python standard library
- Existing Bowser dependencies (GTK, Skia)

**Optional:**
- Graphviz (`dot` command) for SVG rendering
  - Install: `sudo apt install graphviz`
  - Gracefully falls back to DOT file if not available

## Example Output

For this HTML:
```html
<html>
  <body>
    <h1>Title</h1>
    <p>Content</p>
  </body>
</html>
```

Generates a graph showing:
- Root `html` node (green)
  - `body` child (green)
    - `h1` child (yellow)
      - "Title" text (blue)
    - `p` child (gray)
      - "Content" text (blue)

## Benefits

1. **Debugging Aid**: Visually inspect parsed DOM structure
2. **Learning Tool**: Understand how HTML is parsed
3. **Structure Validation**: Verify element nesting and hierarchy
4. **Development**: Quickly check if DOM building works correctly

## Future Enhancements

Potential improvements:
- Add CSS selector highlighting
- Show computed styles on nodes
- Interactive graph (clickable nodes)
- Export to different formats (PNG, PDF)
- Side-by-side HTML source comparison
- DOM mutation tracking
