"""Pytest configuration and fixtures."""

import pytest
import logging


@pytest.fixture(autouse=True)
def configure_logging():
    """Configure logging for tests."""
    logging.basicConfig(
        level=logging.WARNING,  # Only show warnings/errors in tests
        format="%(name)s %(levelname)s: %(message)s",
    )


@pytest.fixture
def mock_browser():
    """Create a mock browser for testing."""
    from unittest.mock import Mock
    browser = Mock()
    browser._log = Mock()
    return browser
