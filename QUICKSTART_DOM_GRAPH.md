# DOM Graph Visualization - Quick Reference

## What is it?
A debugging tool that visualizes the Document Object Model (DOM) tree of the currently loaded web page as a graph.

## How to use it?
Press **Ctrl+Shift+D** while viewing any page in Bowser.

## What you get

### 1. Console Output
```
DOM TREE STRUCTURE:
====================
<html>
  <body>
    <h1>
      Text: 'Page Title'
    <p>
      Text: 'Page content...'
```

### 2. New Browser Tab
- Automatically opens with the visualization
- Clean, dark-themed interface
- Color legend explaining node colors
- Interactive SVG graph (if Graphviz installed)
- DOT format view with installation instructions (without Graphviz)

### 3. Graph File
Saved to `~/.cache/bowser/dom_graph.svg` (or `.dot` without Graphviz)

## Node Colors

| Color | Elements |
|-------|----------|
| 🟢 Light Green | `<html>`, `<body>` |
| 🟡 Light Yellow | `<h1>`, `<h2>`, `<h3>`, `<h4>`, `<h5>`, `<h6>` |
| ⚪ Light Gray | `<div>`, `<p>`, `<span>` |
| 🔵 Light Cyan | `<ul>`, `<ol>`, `<li>` |
| 🔴 Light Pink | `<a>`, `<button>` |
| 🔵 Light Blue | Text nodes |
| ⚪ White | Other elements |

## Installation (Optional)

For visual graphs, install Graphviz:
```bash
sudo apt install graphviz
```

Without it, you'll get a `.dot` file that you can:
- View with any text editor
- Render online at http://webgraphviz.com
- Render manually: `dot -Tsvg dom_graph.dot -o output.svg`

## Test it!

1. Load the test page:
   ```bash
   uv run bowser file://$(pwd)/test_dom.html
   ```

2. Press **Ctrl+Shift+D**

3. View the generated graph!

## Files

- **Implementation**: `src/debug/dom_graph.py`
- **Tests**: `tests/test_dom_graph.py` (10/10 passing)
- **Docs**: `docs/DOM_VISUALIZATION.md`
- **Example**: `test_dom.html`

## Benefits

- 🔍 **Debug**: Quickly inspect DOM structure
- 📚 **Learn**: Understand HTML parsing
- ✅ **Validate**: Check element hierarchy
- 🎨 **Visualize**: See the tree structure clearly
