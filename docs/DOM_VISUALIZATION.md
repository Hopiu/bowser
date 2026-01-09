# DOM Visualization Feature

## Overview

The DOM visualization feature allows you to inspect the Document Object Model (DOM) tree of the currently loaded page as a graph. This is useful for debugging, understanding page structure, and learning how browsers parse HTML.

## Usage

### Keyboard Shortcut

Press **Ctrl+Shift+D** while viewing any page to generate a DOM graph.

### What Happens

1. **Console Output**: The DOM tree structure is printed to the console in text format
2. **Graph File**: A graph file is generated in `~/.cache/bowser/`
3. **New Browser Tab**: Opens automatically displaying the visualization
   - Shows interactive SVG graph (if Graphviz installed)
   - Shows DOT format with installation instructions (if Graphviz not installed)

### Graph Features

- **Color-Coded Nodes**: Different element types have different colors
  - Light green: `<html>`, `<body>`
  - Light yellow: Headings (`<h1>`, `<h2>`, etc.)
  - Light gray: Block elements (`<div>`, `<p>`, `<span>`)
  - Light cyan: Lists (`<ul>`, `<ol>`, `<li>`)
  - Light pink: Interactive elements (`<a>`, `<button>`)
  - White: Other elements

- **Node Labels**: Show element tags and up to 3 attributes
- **Text Nodes**: Display text content (truncated to 50 characters)
- **Hierarchical Layout**: Shows parent-child relationships with arrows

## Installation (Optional)

For visual graph rendering, install Graphviz:

```bash
# Debian/Ubuntu
sudo apt install graphviz

# macOS
brew install graphviz

# Fedora
sudo dnf install graphviz
```

Without Graphviz, the tool will save a `.dot` file that you can:
- Open with a text editor to see the graph definition
- Render online at http://www.webgraphviz.com/
- Render with `dot -Tsvg dom_graph.dot -o dom_graph.svg`

## Output Files

All generated files are saved to `~/.cache/bowser/`:
- `dom_graph.svg` - Visual graph (if Graphviz available)
- `dom_graph.dot` - Graph definition in DOT format

## Examples

### Simple Page
```html
<html>
  <body>
    <h1>Title</h1>
    <p>Content</p>
  </body>
</html>
```

Will generate a graph showing:
```
html (green) → body (green) → h1 (yellow) → "Title" (blue text node)
                            → p (gray) → "Content" (blue text node)
```

### Testing

A test page is included at `test_dom.html`. Open it with:
```bash
uv run bowser file://$(pwd)/test_dom.html
```

Then press Ctrl+Shift+D to visualize its DOM structure.

## Implementation

The visualization is implemented in:
- `src/debug/dom_graph.py` - Graph generation logic
- `src/browser/chrome.py` - Keyboard shortcut handler

The feature uses:
- **Graphviz DOT format** for graph definition
- **Recursive tree traversal** to build node hierarchy
- **GTK keyboard event handling** for the shortcut
