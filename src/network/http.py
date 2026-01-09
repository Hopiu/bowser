"""HTTP requests and response handling."""

import http.client
from typing import Optional, Tuple
import logging

from .url import URL


def request(url: URL, payload: Optional[bytes] = None, method: str = "GET", max_redirects: int = 10) -> Tuple[int, str, bytes]:
    """
    Fetch a URL and follow redirects, returning (status_code, content_type, body).
    
    Args:
        url: URL to fetch
        payload: Optional request body
        method: HTTP method (GET, POST, etc.)
        max_redirects: Maximum number of redirects to follow (default 10)
    
    Returns:
        Tuple of (status_code, content_type, response_body)
    """
    logger = logging.getLogger("bowser.network")
    current_url = url
    redirect_count = 0
    
    while redirect_count < max_redirects:
        parsed = current_url._parsed
        conn_class = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
        
        try:
            conn = conn_class(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
            path = parsed.path or "/"
            if parsed.query:
                path = f"{path}?{parsed.query}"
            
            headers = {
                "User-Agent": "Bowser/0.0.1",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
            
            logger.info(f"HTTP {method} {parsed.scheme}://{parsed.hostname}{path}")
            conn.request(method, path, body=payload, headers=headers)
            resp = conn.getresponse()
            
            status = resp.status
            content_type = resp.getheader("Content-Type", "text/html")
            body = resp.read()
            
            logger.info(f"HTTP response {status} {resp.reason} ({len(body)} bytes)")
            
            # Handle redirects (3xx status codes)
            if 300 <= status < 400 and status != 304:
                location = resp.getheader("Location")
                conn.close()
                
                if not location:
                    logger.warning(f"Redirect response {status} without Location header")
                    return status, content_type, body
                
                logger.info(f"Following redirect to {location}")
                redirect_count += 1
                
                # Convert relative URLs to absolute
                if location.startswith("http://") or location.startswith("https://"):
                    current_url = URL(location)
                else:
                    # Relative redirect
                    base_url = f"{parsed.scheme}://{parsed.hostname}"
                    if parsed.port:
                        base_url += f":{parsed.port}"
                    current_url = URL(base_url + location)
                
                # For 303 (See Other), change method to GET
                if status == 303:
                    method = "GET"
                    payload = None
                
                continue
            
            conn.close()
            return status, content_type, body
            
        except Exception as e:
            logger.error(f"HTTP request failed: {e}")
            raise
    
    # Max redirects exceeded
    logger.error(f"Maximum redirects ({max_redirects}) exceeded")
    raise Exception(f"Too many redirects (max: {max_redirects})")
