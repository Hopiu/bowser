"""Tests for HTTP functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.network.url import URL
from src.network import http


class TestHTTPRequest:
    @patch('src.network.http.http.client.HTTPConnection')
    def test_http_request_success(self, mock_conn_class):
        # Setup mock
        mock_conn = Mock()
        mock_response = Mock()
        mock_response.status = 200
        mock_response.reason = "OK"
        mock_response.getheader.return_value = "text/html"
        mock_response.read.return_value = b"<html>Hello</html>"
        
        mock_conn.getresponse.return_value = mock_response
        mock_conn_class.return_value = mock_conn
        
        # Test
        url = URL("http://example.com/page")
        status, content_type, body = http.request(url)
        
        assert status == 200
        assert content_type == "text/html"
        assert body == b"<html>Hello</html>"
        
    @patch('src.network.http.http.client.HTTPSConnection')
    def test_https_request(self, mock_conn_class):
        # Setup mock
        mock_conn = Mock()
        mock_response = Mock()
        mock_response.status = 200
        mock_response.reason = "OK"
        mock_response.getheader.return_value = "text/html"
        mock_response.read.return_value = b"Secure content"
        
        mock_conn.getresponse.return_value = mock_response
        mock_conn_class.return_value = mock_conn
        
        # Test
        url = URL("https://example.com")
        status, content_type, body = http.request(url)
        
        assert status == 200
        assert b"Secure" in body
        mock_conn_class.assert_called_once()
        
    @patch('src.network.http.http.client.HTTPConnection')
    def test_http_request_404(self, mock_conn_class):
        # Setup mock
        mock_conn = Mock()
        mock_response = Mock()
        mock_response.status = 404
        mock_response.reason = "Not Found"
        mock_response.getheader.return_value = "text/html"
        mock_response.read.return_value = b"<html>Not Found</html>"
        
        mock_conn.getresponse.return_value = mock_response
        mock_conn_class.return_value = mock_conn
        
        # Test
        url = URL("http://example.com/missing")
        status, content_type, body = http.request(url)
        
        assert status == 404
        
    @patch('src.network.http.http.client.HTTPConnection')
    def test_http_request_with_user_agent(self, mock_conn_class):
        # Setup mock
        mock_conn = Mock()
        mock_response = Mock()
        mock_response.status = 200
        mock_response.reason = "OK"
        mock_response.getheader.return_value = "text/html"
        mock_response.read.return_value = b"content"
        
        mock_conn.getresponse.return_value = mock_response
        mock_conn_class.return_value = mock_conn
        
        # Test
        url = URL("http://example.com")
        http.request(url)
        
        # Verify User-Agent header was sent
        call_args = mock_conn.request.call_args
        headers = call_args[1]['headers']
        assert 'User-Agent' in headers
        assert 'Bowser' in headers['User-Agent']
    
    @patch('src.network.http.http.client.HTTPConnection')
    def test_http_redirect_301(self, mock_conn_class):
        """Test following 301 permanent redirect."""
        # Setup mock for first request (redirect)
        mock_conn = Mock()
        mock_response_redirect = Mock()
        mock_response_redirect.status = 301
        mock_response_redirect.reason = "Moved Permanently"
        mock_response_redirect.getheader.side_effect = lambda header, default="": {
            "Content-Type": "text/html",
            "Location": "http://example.com/new-page"
        }.get(header, default)
        mock_response_redirect.read.return_value = b"<html>Redirect</html>"
        
        # Setup mock for second request (final response)
        mock_response_final = Mock()
        mock_response_final.status = 200
        mock_response_final.reason = "OK"
        mock_response_final.getheader.side_effect = lambda header, default="": {
            "Content-Type": "text/html",
        }.get(header, default)
        mock_response_final.read.return_value = b"<html>Final content</html>"
        
        mock_conn.getresponse.side_effect = [mock_response_redirect, mock_response_final]
        mock_conn_class.return_value = mock_conn
        
        # Test
        url = URL("http://example.com/old-page")
        status, content_type, body = http.request(url)
        
        assert status == 200
        assert body == b"<html>Final content</html>"
        assert mock_conn.request.call_count == 2
    
    @patch('src.network.http.http.client.HTTPConnection')
    def test_http_redirect_302(self, mock_conn_class):
        """Test following 302 temporary redirect."""
        # Setup mock for first request (redirect)
        mock_conn = Mock()
        mock_response_redirect = Mock()
        mock_response_redirect.status = 302
        mock_response_redirect.reason = "Found"
        mock_response_redirect.getheader.side_effect = lambda header, default="": {
            "Content-Type": "text/html",
            "Location": "http://example.com/temp-page"
        }.get(header, default)
        mock_response_redirect.read.return_value = b"<html>Redirect</html>"
        
        # Setup mock for second request (final response)
        mock_response_final = Mock()
        mock_response_final.status = 200
        mock_response_final.reason = "OK"
        mock_response_final.getheader.side_effect = lambda header, default="": {
            "Content-Type": "text/html",
        }.get(header, default)
        mock_response_final.read.return_value = b"<html>Temp content</html>"
        
        mock_conn.getresponse.side_effect = [mock_response_redirect, mock_response_final]
        mock_conn_class.return_value = mock_conn
        
        # Test
        url = URL("http://example.com/old-page")
        status, content_type, body = http.request(url)
        
        assert status == 200
        assert body == b"<html>Temp content</html>"
    
    @patch('src.network.http.http.client.HTTPConnection')
    def test_http_redirect_no_location(self, mock_conn_class):
        """Test handling of redirect without Location header."""
        # Setup mock
        mock_conn = Mock()
        mock_response = Mock()
        mock_response.status = 302
        mock_response.reason = "Found"
        mock_response.getheader.side_effect = lambda header, default="": {
            "Content-Type": "text/html",
        }.get(header, default)
        mock_response.read.return_value = b"<html>Redirect</html>"
        
        mock_conn.getresponse.return_value = mock_response
        mock_conn_class.return_value = mock_conn
        
        # Test
        url = URL("http://example.com/page")
        status, content_type, body = http.request(url)
        
        # Should return the redirect response if no Location header
        assert status == 302
        assert body == b"<html>Redirect</html>"
    
    @patch('src.network.http.http.client.HTTPConnection')
    def test_http_max_redirects(self, mock_conn_class):
        """Test that max redirects limit is enforced."""
        # Setup mock that always returns a redirect
        mock_conn = Mock()
        mock_response = Mock()
        mock_response.status = 302
        mock_response.reason = "Found"
        mock_response.getheader.side_effect = lambda header, default="": {
            "Location": "http://example.com/redirect-loop"
        }.get(header, default)
        mock_response.read.return_value = b""
        
        mock_conn.getresponse.return_value = mock_response
        mock_conn_class.return_value = mock_conn
        
        # Test with max_redirects=2
        url = URL("http://example.com/page")
        with pytest.raises(Exception, match="Too many redirects"):
            http.request(url, max_redirects=2)
