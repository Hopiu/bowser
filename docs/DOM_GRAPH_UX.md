# DOM Graph Visualization - User Experience

## What You'll See

When you press **Ctrl+Shift+D**, a new tab automatically opens with this view:

```
┌─────────────────────────────────────────────────────────────────┐
│ 🌳 DOM Tree Visualization                                      │
│ Source: /home/user/.cache/bowser/dom_graph.svg                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Color Legend:                                                   │
│ ┌─────────┬──────────────────────────────────────────────┐    │
│ │ 🟢      │ <html>, <body>                              │    │
│ │ 🟡      │ Headings (h1-h6)                            │    │
│ │ ⚪      │ Block elements                               │    │
│ │ 🔵      │ Lists (ul, ol, li)                          │    │
│ │ 🔴      │ Interactive (a, button)                     │    │
│ │ 🔵      │ Text nodes                                   │    │
│ └─────────┴──────────────────────────────────────────────┘    │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────┐   │
│ │                                                         │   │
│ │              [Visual DOM Graph Here]                    │   │
│ │                                                         │   │
│ │         html ──┬── body ──┬── h1 ── "Title"           │   │
│ │                           │                             │   │
│ │                           ├── p ── "Content"           │   │
│ │                           │                             │   │
│ │                           └── ul ──┬── li ── "Item 1" │   │
│ │                                    └── li ── "Item 2" │   │
│ │                                                         │   │
│ └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│ Bowser Browser • DOM Graph Visualization • Ctrl+Shift+D       │
└─────────────────────────────────────────────────────────────────┘
```

## Interface Elements

### Header (Dark Gray)
- 🌳 Title with icon
- File path showing where graph is saved
- Clean, minimal design

### Color Legend
- Explains what each color means
- 6 different node types
- Easy reference while viewing graph

### Graph Display
**With Graphviz (SVG):**
- Beautiful vector graphics
- Zoomable/scalable
- Clean node layout
- Clear hierarchy

**Without Graphviz (DOT):**
- Installation instructions
- Raw DOT format shown
- Helpful hints for rendering

### Footer (Dark Gray)
- Branding
- Keyboard shortcut reminder

## Color Scheme

**Background:**
- Dark: `#1e1e1e` (VS Code inspired)
- Cards: `#2d2d2d`
- Borders: `#3e3e3e`

**Text:**
- Primary: `#d4d4d4`
- Accent: `#4ec9b0` (teal/green)
- Muted: `#858585`

**Graph Nodes:**
- Exactly as in the generated SVG
- Matches console output colors

## Workflow

```
┌──────────────────────────────────────────────────────────┐
│  1. You're viewing a page                               │
│     (e.g., example.com)                                 │
└──────────────────────────────────────────────────────────┘
                      ↓
         Press Ctrl+Shift+D
                      ↓
┌──────────────────────────────────────────────────────────┐
│  2. Console Output (Terminal)                           │
│     ═══════════════════════════════                     │
│     DOM TREE STRUCTURE:                                 │
│     <html>                                              │
│       <body>                                            │
│         <h1>                                            │
│           Text: 'Example'                               │
└──────────────────────────────────────────────────────────┘
                      ↓
         (simultaneously)
                      ↓
┌──────────────────────────────────────────────────────────┐
│  3. New Tab Opens                                       │
│     about:dom-graph?path=/home/.../.cache/...svg        │
│                                                          │
│     Shows beautiful visualization with:                 │
│     • Color legend                                      │
│     • Interactive graph                                 │
│     • Dark theme                                        │
└──────────────────────────────────────────────────────────┘
                      ↓
         Keep working!
                      ↓
┌──────────────────────────────────────────────────────────┐
│  4. Continue browsing                                   │
│     • Graph tab stays open                              │
│     • Switch back anytime                               │
│     • Generate new graphs anytime                       │
└──────────────────────────────────────────────────────────┘
```

## Comparison

### Before (External Viewer)
```
Browser → Ctrl+Shift+D → xdg-open → SVG Viewer
  ↓                                      ↑
  └──────── Switch apps ────────────────┘
```

### After (Browser Tab)
```
Browser → Ctrl+Shift+D → New Tab → View Graph
  └────────── All in Bowser ────────────┘
```

## Advantages

1. **No App Switching** - Everything in browser
2. **Consistent UX** - Same interface as other pages
3. **Always Available** - No need for external apps
4. **Better Integration** - Part of your browsing session
5. **More Features** - Legend, hints, instructions
6. **Beautiful Design** - Custom dark theme
7. **Responsive** - Works at any size

## Next Steps

Try it yourself:
1. Open Bowser
2. Navigate to any page (or use the test page)
3. Press **Ctrl+Shift+D**
4. Enjoy the beautiful DOM visualization!
