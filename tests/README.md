# Bowser Test Suite

This directory contains the test suite for the Bowser browser.

## Running Tests

Run all tests:
```bash
uv run pytest
```

Run with verbose output:
```bash
uv run pytest -v
```

Run specific test file:
```bash
uv run pytest tests/test_browser.py
```

Run with coverage:
```bash
uv run pytest --cov=src --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html
```

## Test Organization

- `test_url.py` - URL parsing and resolution
- `test_parser.py` - HTML/CSS parsing
- `test_browser.py` - Browser and tab management
- `test_cookies.py` - Cookie jar functionality
- `test_layout.py` - Layout engine components
- `test_render.py` - Rendering primitives
- `conftest.py` - Shared fixtures and configuration

## Writing Tests

Tests use pytest. Example:

```python
def test_feature():
    # Arrange
    obj = MyClass()
    
    # Act
    result = obj.method()
    
    # Assert
    assert result == expected
```

Use mocks for GTK components:
```python
@patch('src.browser.browser.Gtk')
def test_with_gtk(mock_gtk):
    browser = Browser()
    # test code
```
