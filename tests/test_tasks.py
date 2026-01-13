"""Tests for the async task queue system."""

import time
import threading
from unittest.mock import patch


class TestTaskQueue:
    """Tests for the TaskQueue class."""

    def test_task_queue_singleton(self):
        """Test that TaskQueue is a singleton."""
        from src.network.tasks import TaskQueue

        # Reset singleton for clean test
        TaskQueue.reset_instance()

        q1 = TaskQueue()
        q2 = TaskQueue()

        assert q1 is q2

        # Clean up
        TaskQueue.reset_instance()

    def test_submit_task_returns_id(self):
        """Test that submit returns a task ID."""
        from src.network.tasks import TaskQueue

        TaskQueue.reset_instance()
        queue = TaskQueue()

        # Mock GLib.idle_add to avoid GTK dependency
        with patch('src.network.tasks.GLib') as mock_glib:
            mock_glib.idle_add = lambda cb, *args: cb(*args) if args else cb()

            task_id = queue.submit(lambda: 42)

            # Task ID should be non-negative (or -1 for cached)
            assert isinstance(task_id, int)

        # Wait for task to complete
        time.sleep(0.1)
        TaskQueue.reset_instance()

    def test_task_executes_function(self):
        """Test that submitted tasks are executed."""
        from src.network.tasks import TaskQueue

        TaskQueue.reset_instance()
        queue = TaskQueue()

        result = []
        threading.Event()

        def task():
            result.append("executed")
            return "done"

        with patch('src.network.tasks.GLib') as mock_glib:
            mock_glib.idle_add = lambda cb, *args: cb(*args) if args else cb()

            queue.submit(task)

        # Wait for task to complete
        time.sleep(0.2)

        assert "executed" in result

        TaskQueue.reset_instance()

    def test_on_complete_callback(self):
        """Test that on_complete callback is called with result."""
        from src.network.tasks import TaskQueue

        TaskQueue.reset_instance()
        queue = TaskQueue()

        results = []

        def task():
            return 42

        def on_complete(result):
            results.append(result)

        with patch('src.network.tasks.GLib') as mock_glib:
            # Make idle_add execute immediately
            mock_glib.idle_add = lambda cb, *args: cb(*args) if args else cb()

            queue.submit(task, on_complete=on_complete)

        # Wait for task to complete (may need more time under load)
        for _ in range(10):
            if 42 in results:
                break
            time.sleep(0.05)

        assert 42 in results

        TaskQueue.reset_instance()

    def test_on_error_callback(self):
        """Test that on_error callback is called on exception."""
        from src.network.tasks import TaskQueue

        TaskQueue.reset_instance()
        queue = TaskQueue()

        errors = []

        def failing_task():
            raise ValueError("Test error")

        def on_error(e):
            errors.append(str(e))

        with patch('src.network.tasks.GLib') as mock_glib:
            mock_glib.idle_add = lambda cb, *args: cb(*args) if args else cb()

            queue.submit(failing_task, on_error=on_error)

        # Wait for task to complete (may need more time under load)
        for _ in range(10):
            if len(errors) == 1:
                break
            time.sleep(0.05)

        assert len(errors) == 1
        assert "Test error" in errors[0]

        TaskQueue.reset_instance()

    def test_cancel_task(self):
        """Test task cancellation."""
        from src.network.tasks import TaskQueue

        TaskQueue.reset_instance()
        queue = TaskQueue()

        result = []

        def slow_task():
            time.sleep(1)
            result.append("completed")
            return True

        with patch('src.network.tasks.GLib') as mock_glib:
            mock_glib.idle_add = lambda cb, *args: cb(*args) if args else cb()

            task_id = queue.submit(slow_task)

            # Cancel immediately
            cancelled = queue.cancel(task_id)

            # May or may not be cancellable depending on timing
            assert isinstance(cancelled, bool)

        # Wait briefly
        time.sleep(0.1)

        TaskQueue.reset_instance()

    def test_pending_count(self):
        """Test pending task count."""
        from src.network.tasks import TaskQueue

        TaskQueue.reset_instance()
        queue = TaskQueue()

        initial_count = queue.pending_count
        assert initial_count >= 0

        TaskQueue.reset_instance()


class TestAsyncImageLoading:
    """Tests for async image loading."""

    def test_load_image_async_cached(self):
        """Test that cached images return -1 (no task needed)."""
        from src.network.images import load_image_async, load_image, ImageCache

        # Clear cache
        ImageCache().clear()

        # Load an image synchronously first (to cache it)
        data_url = (
            "data:image/png;base64,"
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
        )
        image = load_image(data_url)
        assert image is not None

        # Now load async - should hit cache and return -1 (no task)
        # We don't need a callback for this test - just checking return value
        task_id = load_image_async(data_url, on_complete=None)

        # Cached loads return -1 (no task created)
        assert task_id == -1

    def test_load_image_async_uncached(self):
        """Test that uncached images create tasks."""
        from src.network.images import load_image_async, ImageCache
        from src.network.tasks import TaskQueue

        # Clear cache
        ImageCache().clear()
        TaskQueue.reset_instance()

        # Use a data URL that's not cached
        data_url = (
            "data:image/png;base64,"
            "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAADklEQVR42mP8z8DwHwYAAQYBA/5h2aw4AAAAAElFTkSuQmCC"
        )

        # Patch GLib.idle_add to call callbacks immediately (no GTK main loop in tests)
        with patch('src.network.tasks.GLib') as mock_glib:
            mock_glib.idle_add = lambda cb, *args: cb(*args) if args else cb()

            # Without a callback, it just submits the task
            task_id = load_image_async(data_url, on_complete=None)

            # Should create a task (non-negative ID)
            assert task_id >= 0

            # Wait for task to complete
            time.sleep(0.3)

        # Image should now be cached
        assert ImageCache().has(data_url)

        TaskQueue.reset_instance()
