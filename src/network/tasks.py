"""Async task queue for background operations like image loading."""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from typing import Callable, Optional, Any
from queue import Queue
import gi

gi.require_version("GLib", "2.0")
from gi.repository import GLib

logger = logging.getLogger("bowser.tasks")


@dataclass
class Task:
    """A task to be executed in the background."""
    
    func: Callable[[], Any]
    on_complete: Optional[Callable[[Any], None]] = None
    on_error: Optional[Callable[[Exception], None]] = None
    priority: int = 0  # Lower = higher priority
    
    def __lt__(self, other):
        return self.priority < other.priority


class TaskQueue:
    """
    Background task queue using a thread pool.
    
    Uses GTK's GLib.idle_add for thread-safe UI updates.
    """
    
    _instance: Optional["TaskQueue"] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "TaskQueue":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, max_workers: int = 4):
        if self._initialized:
            return
            
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="bowser-task"
        )
        self._pending: dict[int, Future] = {}
        self._task_id = 0
        self._task_lock = threading.Lock()
        self._initialized = True
        self._shutdown = False
        
        logger.debug(f"TaskQueue initialized with {max_workers} workers")
    
    def submit(
        self,
        func: Callable[[], Any],
        on_complete: Optional[Callable[[Any], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
    ) -> int:
        """
        Submit a task for background execution.
        
        Args:
            func: Function to run in background (no arguments)
            on_complete: Callback with result (runs on main thread)
            on_error: Callback with exception (runs on main thread)
            
        Returns:
            Task ID that can be used to cancel
        """
        if self._shutdown:
            logger.warning("TaskQueue is shutdown, ignoring task")
            return -1
            
        with self._task_lock:
            task_id = self._task_id
            self._task_id += 1
        
        def wrapped():
            try:
                result = func()
                if on_complete:
                    # Schedule callback on main GTK thread
                    GLib.idle_add(self._call_on_main, on_complete, result)
                return result
            except Exception as e:
                logger.error(f"Task {task_id} failed: {e}")
                if on_error:
                    GLib.idle_add(self._call_on_main, on_error, e)
                raise
            finally:
                with self._task_lock:
                    self._pending.pop(task_id, None)
        
        future = self._executor.submit(wrapped)
        
        with self._task_lock:
            self._pending[task_id] = future
        
        logger.debug(f"Submitted task {task_id}")
        return task_id
    
    def _call_on_main(self, callback: Callable, arg: Any) -> bool:
        """Execute a callback on the main thread. Returns False to remove from idle."""
        try:
            callback(arg)
        except Exception as e:
            logger.error(f"Callback error: {e}")
        return False  # Don't repeat
    
    def cancel(self, task_id: int) -> bool:
        """Cancel a pending task. Returns True if cancelled."""
        with self._task_lock:
            future = self._pending.get(task_id)
            if future:
                cancelled = future.cancel()
                if cancelled:
                    self._pending.pop(task_id, None)
                    logger.debug(f"Cancelled task {task_id}")
                return cancelled
        return False
    
    def cancel_all(self):
        """Cancel all pending tasks."""
        with self._task_lock:
            for task_id, future in list(self._pending.items()):
                future.cancel()
            self._pending.clear()
        logger.debug("Cancelled all tasks")
    
    @property
    def pending_count(self) -> int:
        """Number of pending tasks."""
        with self._task_lock:
            return len(self._pending)
    
    def shutdown(self, wait: bool = True):
        """Shutdown the task queue."""
        self._shutdown = True
        self.cancel_all()
        self._executor.shutdown(wait=wait)
        logger.debug("TaskQueue shutdown")
    
    @classmethod
    def reset_instance(cls):
        """Reset the singleton (for testing)."""
        with cls._lock:
            if cls._instance and cls._instance._initialized:
                cls._instance.shutdown(wait=False)
            cls._instance = None


# Convenience functions
def submit_task(
    func: Callable[[], Any],
    on_complete: Optional[Callable[[Any], None]] = None,
    on_error: Optional[Callable[[Exception], None]] = None,
) -> int:
    """Submit a task to the global task queue."""
    return TaskQueue().submit(func, on_complete, on_error)


def cancel_task(task_id: int) -> bool:
    """Cancel a task in the global queue."""
    return TaskQueue().cancel(task_id)
