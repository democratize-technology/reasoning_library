"""
Reasoning Engine Module with Async Context Manager

ID-005 FIX: This module provides secure async context managers with proper
resource cleanup to prevent memory leaks and resource exhaustion.

The implementation addresses:
- Unclosed file handles and connections leading to resource exhaustion
- Memory leak in async context manager implementation
- Potential denial of service through memory exhaustion
- Proper resource cleanup patterns for async operations
"""

import asyncio
import gc
import os
import tempfile
import time
import threading
import weakref
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, AsyncIterator, Callable, Union
from dataclasses import dataclass, field
from pathlib import Path
import logging

from .exceptions import ValidationError
from .constants import MAX_SOURCE_CODE_SIZE


@dataclass
class ResourceMetrics:
    """Metrics for tracking resource usage in context managers."""
    active_connections: int = 0
    open_files: int = 0
    memory_usage_bytes: int = 0
    peak_connections: int = 0
    peak_files: int = 0
    cleanup_operations: int = 0
    cleanup_errors: int = 0


class ResourceManager:
    """
    Centralized resource manager for tracking and cleaning up resources.

    This class provides thread-safe resource tracking and ensures that
    all resources are properly cleaned up to prevent memory leaks.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._active_resources: Dict[str, weakref.ref] = {}
        self._resource_types: Dict[str, str] = {}  # Track resource type at registration
        self._cleanup_callbacks: List[Callable] = []
        self._metrics = ResourceMetrics()
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)

        # Register cleanup handler for process exit
        import atexit
        atexit.register(self.cleanup_all_resources)

    def register_resource(self, resource_id: str, resource: Any, cleanup_callback: Optional[Callable] = None):
        """
        Register a resource for tracking.

        Args:
            resource_id: Unique identifier for the resource
            resource: The resource to track
            cleanup_callback: Optional callback for cleanup
        """
        with self._lock:
            # Use weak reference to prevent circular references
            self._active_resources[resource_id] = weakref.ref(resource)

            if cleanup_callback:
                self._cleanup_callbacks.append(cleanup_callback)

            # Determine resource type and update metrics based on registration state
            resource_type = None
            if hasattr(resource, 'is_open') and resource.is_open:
                resource_type = 'connection'
                self._metrics.active_connections += 1
                self._metrics.peak_connections = max(self._metrics.peak_connections, self._metrics.active_connections)
            elif hasattr(resource, 'closed') and not resource.closed:
                resource_type = 'file'
                self._metrics.open_files += 1
                self._metrics.peak_files = max(self._metrics.peak_files, self._metrics.open_files)

            # Store the resource type at registration time for accurate cleanup
            if resource_type:
                self._resource_types[resource_id] = resource_type

    def unregister_resource(self, resource_id: str):
        """
        Unregister a resource.

        Args:
            resource_id: ID of the resource to unregister
        """
        with self._lock:
            if resource_id in self._active_resources:
                ref = self._active_resources.pop(resource_id)
                resource_type = self._resource_types.pop(resource_id, None)
                resource = ref() if ref else None

                # Decrement metrics based on registration state, not current state
                if resource_type == 'connection':
                    self._metrics.active_connections = max(0, self._metrics.active_connections - 1)
                elif resource_type == 'file':
                    self._metrics.open_files = max(0, self._metrics.open_files - 1)

    async def cleanup_resource(self, resource_id: str) -> bool:
        """
        Clean up a specific resource.

        Args:
            resource_id: ID of the resource to clean up

        Returns:
            True if cleanup was successful, False otherwise
        """
        with self._lock:
            if resource_id not in self._active_resources:
                return True

            ref = self._active_resources.pop(resource_id)
            resource = ref() if ref else None

            if not resource:
                return True

            try:
                # Try async cleanup first
                if hasattr(resource, 'aclose'):
                    await resource.aclose()
                elif hasattr(resource, 'close'):
                    if asyncio.iscoroutinefunction(resource.close):
                        await resource.close()
                    else:
                        resource.close()
                elif hasattr(resource, '__aexit__'):
                    await resource.__aexit__(None, None, None)
                elif hasattr(resource, '__exit__'):
                    resource.__exit__(None, None, None)

                self._metrics.cleanup_operations += 1
                return True

            except Exception as e:
                self._metrics.cleanup_errors += 1
                self._logger.warning(f"Error cleaning up resource {resource_id}: {e}")
                return False

    def cleanup_all_resources(self):
        """Clean up all registered resources."""
        with self._lock:
            resource_ids = list(self._active_resources.keys())

            for resource_id in resource_ids:
                # Use asyncio.run if in sync context
                try:
                    if asyncio.get_event_loop().is_running():
                        # Create a task for async cleanup
                        asyncio.create_task(self.cleanup_resource(resource_id))
                    else:
                        asyncio.run(self.cleanup_resource(resource_id))
                except Exception:
                    # Fallback to sync cleanup
                    try:
                        self.unregister_resource(resource_id)
                    except Exception:
                        pass

            # Clean up resource types mapping in case any were missed
            self._resource_types.clear()

        # Execute any registered cleanup callbacks
        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                self._logger.warning(f"Error in cleanup callback: {e}")

    def get_metrics(self) -> ResourceMetrics:
        """Get current resource metrics."""
        with self._lock:
            # Update current memory usage
            try:
                import psutil
                process = psutil.Process()
                self._metrics.memory_usage_bytes = process.memory_info().rss
            except ImportError:
                pass

            return ResourceMetrics(**self._metrics.__dict__)


class AsyncFileContext:
    """
    Async context manager for file operations with proper resource cleanup.

    This class ensures that all file handles are properly closed even in
    the presence of exceptions or cancellation.
    """

    def __init__(self, file_path: Union[str, Path], mode: str = 'r', **kwargs):
        self.file_path = Path(file_path)
        self.mode = mode
        self.kwargs = kwargs
        self.file_handle = None
        self.resource_manager = ResourceManager()
        self.resource_id = f"file_{id(self)}_{time.time()}"

    async def __aenter__(self):
        """Open file and register with resource manager."""
        try:
            # Create parent directories if needed
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

            # Open file asynchronously
            loop = asyncio.get_event_loop()
            self.file_handle = await loop.run_in_executor(
                None,
                lambda: open(self.file_path, self.mode, **self.kwargs)
            )

            # Register with resource manager
            self.resource_manager.register_resource(
                self.resource_id,
                self.file_handle
            )

            return self.file_handle

        except Exception as e:
            # Cleanup on failure
            await self._cleanup_on_error()
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close file and unregister from resource manager."""
        await self._cleanup_resources()
        return False  # Don't suppress exceptions

    async def _cleanup_resources(self):
        """Internal cleanup method."""
        if self.file_handle:
            try:
                # Close file handle
                if not self.file_handle.closed:
                    self.file_handle.close()

                # Unregister from resource manager
                self.resource_manager.unregister_resource(self.resource_id)

            except Exception:
                # Log but don't raise cleanup errors
                logging.getLogger(__name__).warning(
                    f"Error during file cleanup for {self.file_path}"
                )
            finally:
                self.file_handle = None

    async def _cleanup_on_error(self):
        """Cleanup method called during __aenter__ failure."""
        await self._cleanup_resources()


class AsyncConnectionContext:
    """
    Async context manager for connection-like resources with proper cleanup.

    This class provides a generic context manager for any async connection
    or resource that needs proper lifecycle management.
    """

    def __init__(self, connection_factory: Callable[[], Any], connection_id: Optional[str] = None):
        self.connection_factory = connection_factory
        self.connection_id = connection_id or f"conn_{id(self)}_{time.time()}"
        self.connection = None
        self.resource_manager = ResourceManager()
        self._cleanup_complete = False

    async def __aenter__(self):
        """Create connection and register with resource manager."""
        try:
            # Create connection
            if asyncio.iscoroutinefunction(self.connection_factory):
                self.connection = await self.connection_factory()
            else:
                self.connection = self.connection_factory()

            # Register with resource manager
            self.resource_manager.register_resource(
                self.connection_id,
                self.connection,
                self._connection_cleanup_callback
            )

            return self.connection

        except Exception as e:
            # Cleanup on failure
            await self._cleanup_on_error()
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close connection and perform cleanup."""
        await self._cleanup_resources()
        return False  # Don't suppress exceptions

    async def _cleanup_resources(self):
        """Internal cleanup method."""
        if self.connection:
            try:
                # Close connection using various methods
                closed_successfully = False

                # Try async close methods
                if hasattr(self.connection, 'aclose'):
                    await self.connection.aclose()
                    closed_successfully = True
                elif hasattr(self.connection, 'close'):
                    if asyncio.iscoroutinefunction(self.connection.close):
                        await self.connection.close()
                    else:
                        self.connection.close()
                    closed_successfully = True

                # Try context manager exit methods
                elif hasattr(self.connection, '__aexit__'):
                    await self.connection.__aexit__(None, None, None)
                    closed_successfully = True
                elif hasattr(self.connection, '__exit__'):
                    self.connection.__exit__(None, None, None)
                    closed_successfully = True

                if closed_successfully:
                    # Unregister from resource manager
                    self.resource_manager.unregister_resource(self.connection_id)

            except Exception:
                # Log but don't raise cleanup errors
                logging.getLogger(__name__).warning(
                    f"Error during connection cleanup for {self.connection_id}"
                )
            finally:
                self.connection = None
                self._cleanup_complete = True

    async def _cleanup_on_error(self):
        """Cleanup method called during __aenter__ failure."""
        await self._cleanup_resources()

    def _connection_cleanup_callback(self):
        """Sync cleanup callback for resource manager."""
        if not self._cleanup_complete and self.connection:
            # Schedule async cleanup if not already done
            try:
                loop = asyncio.get_event_loop()
                if not loop.is_closed():
                    loop.create_task(self._cleanup_resources())
            except Exception:
                # Fallback: try sync cleanup
                try:
                    if hasattr(self.connection, 'close') and not asyncio.iscoroutinefunction(self.connection.close):
                        self.connection.close()
                except Exception:
                    pass


@asynccontextmanager
async def secure_file_context(file_path: Union[str, Path], mode: str = 'r', **kwargs) -> AsyncIterator[Any]:
    """
    Secure async context manager for file operations with ID-005 memory leak fix.

    This context manager ensures that:
    - File handles are always properly closed
    - Resources are tracked for monitoring
    - Memory leaks are prevented through proper cleanup
    - Exceptions don't leave resources open

    Args:
        file_path: Path to the file
        mode: File open mode
        **kwargs: Additional arguments for file opening

    Yields:
        File handle for I/O operations

    Example:
        async with secure_file_context('data.txt', 'w') as f:
            await f.write('Hello World')
        # File is automatically closed here
    """
    context = AsyncFileContext(file_path, mode, **kwargs)
    async with context as file_handle:
        yield file_handle


@asynccontextmanager
async def secure_connection_context(connection_factory: Callable[[], Any], connection_id: Optional[str] = None) -> AsyncIterator[Any]:
    """
    Secure async context manager for connection-like resources with ID-005 memory leak fix.

    This context manager ensures that:
    - Connections are always properly closed
    - Resources are tracked for monitoring
    - Memory leaks are prevented through proper cleanup
    - Both sync and async cleanup methods are supported

    Args:
        connection_factory: Function or coroutine that creates the connection
        connection_id: Optional identifier for the connection

    Yields:
        Connection object

    Example:
        async def create_connection():
            return SomeAsyncConnection()

        async with secure_connection_context(create_connection, 'my_conn') as conn:
            result = await conn.execute_query('SELECT * FROM table')
        # Connection is automatically closed here
    """
    context = AsyncConnectionContext(connection_factory, connection_id)
    async with context as connection:
        yield connection


def get_resource_metrics() -> ResourceMetrics:
    """
    Get current resource usage metrics.

    Returns:
        ResourceMetrics object containing current usage statistics
    """
    return ResourceManager().get_metrics()


def cleanup_all_resources():
    """
    Clean up all registered resources.

    This function is useful for testing or when shutting down
    an application to ensure all resources are properly released.
    """
    ResourceManager().cleanup_all_resources()


# Global resource manager instance
_resource_manager = ResourceManager()

# Export the main functions and classes
__all__ = [
    'AsyncFileContext',
    'AsyncConnectionContext',
    'ResourceMetrics',
    'ResourceManager',
    'secure_file_context',
    'secure_connection_context',
    'get_resource_metrics',
    'cleanup_all_resources'
]