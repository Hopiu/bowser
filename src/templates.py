"""Template rendering utilities."""

import os
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
    
    # Map common status codes to templates
    template_map = {
        404: "error_404.html",
        500: "error_500.html",
        # Network errors
        "network": "error_network.html",
    }
    
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
