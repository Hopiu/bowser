"""Template rendering utilities."""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
import logging


def get_template_env():
    """Get Jinja2 template environment."""
    # Get the assets/pages directory relative to the project root
    # The templates.py file is at src/templates.py, so parent.parent gets to project root
    current_file = Path(__file__)
    pages_dir = current_file.parent.parent / "assets" / "pages"

    # If pages_dir doesn't exist, try alternative path (for tests)
    if not pages_dir.exists():
        pages_dir = Path("/home/bw/Workspace/bowser/assets/pages")

    env = Environment(
        loader=FileSystemLoader(str(pages_dir)),
        autoescape=select_autoescape(['html', 'xml'])
    )
    return env


def render_template(template_name: str, **context) -> str:
    """
    Render a template with the given context.

    Args:
        template_name: Name of the template file (e.g., 'startpage.html')
        **context: Variables to pass to the template

    Returns:
        Rendered HTML string
    """
    logger = logging.getLogger("bowser.templates")

    try:
        env = get_template_env()
        template = env.get_template(template_name)

        # Set default version if not provided
        if 'version' not in context:
            context['version'] = '0.0.1'

        logger.debug(f"Rendering template: {template_name}")
        return template.render(**context)
    except Exception as e:
        logger.error(f"Failed to render template {template_name}: {e}")
        raise


def render_error_page(status_code: int, url: str = "", error_message: str = "") -> str:
    """
    Render an error page for the given status code.

    Args:
        status_code: HTTP status code (404, 500, etc.)
        url: URL that caused the error
        error_message: Optional error details

    Returns:
        Rendered error HTML
    """
    logger = logging.getLogger("bowser.templates")

    # Determine template per status

    if status_code == 404:
        template = "error_404.html"
    elif status_code >= 500:
        template = "error_500.html"
    else:
        template = "error_network.html"

    try:
        env = get_template_env()
        tmpl = env.get_template(template)
        return tmpl.render(
            status_code=status_code,
            url=url,
            error_message=error_message,
            version='0.0.1'
        )
    except Exception as e:
        logger.error(f"Failed to render error page {status_code}: {e}")
        # Return a basic fallback error message
        return f"<html><body><h1>Error {status_code}</h1><p>{error_message}</p></body></html>"


def render_startpage() -> str:
    """Render the startpage."""
    return render_template("startpage.html")


def render_dom_graph_page(graph_path: str) -> str:
    """
    Render the DOM graph visualization page.

    Args:
        graph_path: Path to the PNG, SVG or DOT file

    Returns:
        Rendered HTML with embedded graph
    """
    from pathlib import Path
    import base64

    logger = logging.getLogger("bowser.templates")
    graph_path_obj = Path(graph_path)

    if not graph_path_obj.exists():
        logger.error(f"Graph file not found: {graph_path}")
        return render_template("dom_graph.html",
                             error="Graph file not found",
                             graph_content="",
                             is_svg=False,
                             is_png=False)

    try:
        # Check file type
        suffix = graph_path_obj.suffix.lower()
        is_svg = suffix == '.svg'
        is_png = suffix == '.png'

        if is_png:
            # Read PNG as binary and convert to base64 data URL
            with open(graph_path, 'rb') as f:
                png_data = f.read()
            graph_content = base64.b64encode(png_data).decode('ascii')
            logger.info(f"Rendering DOM graph (PNG) from {graph_path}")
        else:
            # Read text content for SVG or DOT
            with open(graph_path, 'r', encoding='utf-8') as f:
                graph_content = f.read()
            logger.info(f"Rendering DOM graph from {graph_path}")

        return render_template("dom_graph.html",
                             graph_content=graph_content,
                             is_svg=is_svg,
                             is_png=is_png,
                             graph_path=str(graph_path),
                             error=None)

    except Exception as e:
        logger.error(f"Failed to read graph file {graph_path}: {e}")
        return render_template("dom_graph.html",
                             error=f"Failed to load graph: {e}",
                             graph_content="",
                             is_svg=False,
                             is_png=False)
