"""DOM tree visualization as a graph."""

import logging
from typing import Optional
from ..parser.html import Element, Text


def generate_dot_graph(document: Optional[Element]) -> str:
    """
    Generate a Graphviz DOT representation of the DOM tree.

    Args:
        document: Root element of the DOM tree

    Returns:
        DOT format string representing the DOM tree
    """
    if not document:
        return 'digraph DOM {\n  label="Empty Document";\n}\n'

    lines = []
    lines.append('digraph DOM {')
    lines.append('  rankdir=TB;')
    lines.append('  node [shape=box, style=filled];')
    lines.append('')

    node_counter = [0]  # mutable counter for unique IDs

    def escape_label(text: str) -> str:
        """Escape special characters for DOT labels."""
        return text.replace('"', '\\"').replace('\n', '\\n')

    def add_node(node, parent_id: Optional[str] = None) -> str:
        """Recursively add nodes to the graph."""
        node_id = f'node_{node_counter[0]}'
        node_counter[0] += 1

        if isinstance(node, Text):
            # Text nodes
            text_preview = node.text[:50] + ('...' if len(node.text) > 50 else '')
            label = escape_label(text_preview)
            lines.append(f'  {node_id} [label="{label}", fillcolor=lightblue, shape=box];')
        elif isinstance(node, Element):
            # Element nodes
            attrs_str = ""
            if node.attributes:
                attrs_list = [f'{k}="{v}"' for k, v in list(node.attributes.items())[:3]]
                if len(node.attributes) > 3:
                    attrs_list.append('...')
                attrs_str = '\\n' + ' '.join(attrs_list)

            label = f'<{escape_label(node.tag)}>{escape_label(attrs_str)}'

            # Color code by tag type
            if node.tag in ('html', 'body'):
                color = 'lightgreen'
            elif node.tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                color = 'lightyellow'
            elif node.tag in ('div', 'span', 'p'):
                color = 'lightgray'
            elif node.tag in ('ul', 'ol', 'li'):
                color = 'lightcyan'
            elif node.tag in ('a', 'button'):
                color = 'lightpink'
            else:
                color = 'white'

            lines.append(f'  {node_id} [label="{label}", fillcolor={color}];')

            # Add edges to children
            if hasattr(node, 'children'):
                for child in node.children:
                    child_id = add_node(child, node_id)
                    lines.append(f'  {node_id} -> {child_id};')

        return node_id

    add_node(document)
    lines.append('}')

    return '\n'.join(lines)


def save_dom_graph(document: Optional[Element], output_path: str) -> bool:
    """
    Save DOM tree as a DOT file.

    Args:
        document: Root element of the DOM tree
        output_path: Path where to save the .dot file

    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger("bowser.debug")

    try:
        dot_content = generate_dot_graph(document)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(dot_content)

        logger.info(f"DOM graph saved to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to save DOM graph: {e}")
        return False


def render_dom_graph_to_svg(document: Optional[Element], output_path: str) -> bool:
    """
    Render DOM tree as an SVG image using Graphviz (if available).

    Args:
        document: Root element of the DOM tree
        output_path: Path where to save the .svg file

    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger("bowser.debug")

    try:
        import subprocess

        dot_content = generate_dot_graph(document)

        # Try to render with graphviz
        result = subprocess.run(
            ['dot', '-Tsvg', '-o', output_path],
            input=dot_content.encode('utf-8'),
            capture_output=True,
            timeout=10
        )

        if result.returncode == 0:
            logger.info(f"DOM graph rendered to {output_path}")
            return True
        else:
            logger.warning(f"Graphviz rendering failed: {result.stderr.decode()}")
            return False

    except FileNotFoundError:
        logger.warning("Graphviz 'dot' command not found. Install graphviz for SVG output.")
        return False
    except Exception as e:
        logger.error(f"Failed to render DOM graph: {e}")
        return False


def render_dom_graph_to_png(document: Optional[Element], output_path: str) -> bool:
    """
    Render DOM tree as a PNG image using Graphviz (if available).

    Args:
        document: Root element of the DOM tree
        output_path: Path where to save the .png file

    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger("bowser.debug")

    try:
        import subprocess

        dot_content = generate_dot_graph(document)

        # Try to render with graphviz
        result = subprocess.run(
            ['dot', '-Tpng', '-o', output_path],
            input=dot_content.encode('utf-8'),
            capture_output=True,
            timeout=10
        )

        if result.returncode == 0:
            logger.info(f"DOM graph rendered to {output_path}")
            return True
        else:
            logger.warning(f"Graphviz rendering failed: {result.stderr.decode()}")
            return False

    except FileNotFoundError:
        logger.warning("Graphviz 'dot' command not found. Install graphviz for PNG output.")
        return False
    except Exception as e:
        logger.error(f"Failed to render DOM graph: {e}")
        return False


def print_dom_tree(node, indent: int = 0, max_depth: int = 10) -> str:
    """
    Generate a text representation of the DOM tree.

    Args:
        node: DOM node to print
        indent: Current indentation level
        max_depth: Maximum depth to traverse

    Returns:
        String representation of the tree
    """
    if indent > max_depth:
        return "  " * indent + "...\n"

    lines = []
    spacer = "  " * indent

    if isinstance(node, Text):
        text_preview = node.text.strip()[:60]
        if text_preview:
            lines.append(f"{spacer}Text: {repr(text_preview)}\n")
    elif isinstance(node, Element):
        attrs_str = ""
        if node.attributes:
            attrs_preview = {k: v for k, v in list(node.attributes.items())[:3]}
            attrs_str = f" {attrs_preview}"

        lines.append(f"{spacer}<{node.tag}>{attrs_str}\n")

        if hasattr(node, 'children'):
            for child in node.children:
                lines.append(print_dom_tree(child, indent + 1, max_depth))

    return "".join(lines)
