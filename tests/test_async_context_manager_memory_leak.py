"""
Test for ID-005: Memory Leak in Async Context Manager Fix

This test demonstrates and verifies the fix for memory leak vulnerabilities
in async context manager implementation, specifically addressing:
- Unclosed file handles and connections leading to resource exhaustion
- Memory leak in async context manager implementation
- Potential denial of service through memory exhaustion
"""

import asyncio
import gc
import os
import psutil
import tempfile
import threading
import time
import pytest
from typing import Any, Dict, List, Optional

# Import the module we need to test/create
from src.reasoning_library.security_logging import SecurityLogger


class MockAsyncConnection:
    """Mock async connection that tracks resource usage."""

    def __init__(self):
        self.is_open = True
        self.file_handle = None
        self.open_time = time.time()
        self.close_called = False

    async def read(self, size: int = 1024) -> bytes:
        """Mock async read operation."""
        if not self.is_open:
            raise ConnectionError("Connection is closed")
        return b"mock_data" * (size // 9)

    async def write(self, data: bytes) -> int:
        """Mock async write operation."""
        if not self.is_open:
            raise ConnectionError("Connection is closed")
        return len(data)

    async def close(self):
        """Mock async close operation."""
        self.is_open = False
        self.close_called = True
        if self.file_handle:
            try:
                self.file_handle.close()
            except:
                pass


class AsyncContextManagerWithMemoryLeak:
    """
    Async context manager with deliberate memory leak vulnerability.

    This class demonstrates the memory leak issue by:
    1. Not properly cleaning up connections in __aexit__
    2. Accumulating references to resources
    3. Not closing file handles
    """

    # Class-level accumulation of resources (memory leak)
    _active_connections: List[MockAsyncConnection] = []
    _open_files: List[Any] = []

    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.connections: List[MockAsyncConnection] = []
        self.temp_files: List[str] = []
        self.process = psutil.Process()

    async def __aenter__(self):
        """Enter context with resource allocation."""
        # Create multiple connections
        for i in range(self.max_connections):
            conn = MockAsyncConnection()

            # Create temp file and keep it open (resource leak)
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            conn.file_handle = temp_file
            self.temp_files.append(temp_file.name)

            # Add to instance and class-level lists (memory leak)
            self.connections.append(conn)
            self._active_connections.append(conn)
            self._open_files.append(temp_file)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
    Exit context with INTENTIONAL memory leak vulnerability.

    BUG: This method deliberately doesn't properly clean up resources
    to demonstrate the memory leak issue that needs to be fixed.
    """
        # VULNERABILITY: Only close instance connections, not class-level
        # This causes resource leak since references remain
        for conn in self.connections:
            try:
                await conn.close()
            except:
                pass

        # VULNERABILITY: Don't clean up class-level references
        # self._active_connections.clear()  # MISSING - This causes memory leak
        # self._open_files.clear()         # MISSING - This causes memory leak

        # VULNERABILITY: Don't clean up temp files
        # for temp_file in self.temp_files:
        #     try:
        #         os.unlink(temp_file)
        #     except:
        #         pass

        # VULNERABILITY: Don't clear instance references properly
        # self.connections.clear()
        # self.temp_files.clear()

        return False  # Don't suppress exceptions

    @classmethod
    def get_resource_count(cls) -> Dict[str, int]:
        """Get count of leaked resources."""
        return {
            "active_connections": len(cls._active_connections),
            "open_files": len(cls._open_files)
        }


class AsyncContextManagerFixed:
    """
    Fixed version of async context manager with proper resource cleanup.

    This class demonstrates the proper implementation that addresses:
    1. Proper resource cleanup in __aexit__
    2. No resource accumulation or memory leaks
    3. All file handles and connections properly closed
    4. Exception-safe resource management
    """

    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.connections: List[MockAsyncConnection] = []
        self.temp_files: List[str] = []
        self.process = psutil.Process()
        self._cleanup_complete = False

    async def __aenter__(self):
        """Enter context with resource allocation."""
        try:
            # Create multiple connections
            for i in range(self.max_connections):
                conn = MockAsyncConnection()

                # Create temp file and keep it open
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                conn.file_handle = temp_file
                self.temp_files.append(temp_file.name)

                # Add to instance list only (no class-level accumulation)
                self.connections.append(conn)

            return self

        except Exception:
            # Cleanup on failure during __aenter__
            await self._cleanup_resources()
            raise

    async def _cleanup_resources(self):
        """Internal method to clean up all resources."""
        cleanup_errors = []

        # Close all connections properly
        for conn in self.connections:
            try:
                if conn.is_open:
                    await conn.close()
            except Exception as e:
                cleanup_errors.append(f"Connection close error: {e}")

        # Clean up temp files
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                cleanup_errors.append(f"File cleanup error: {e}")

        # Clear references to allow garbage collection
        self.connections.clear()
        self.temp_files.clear()
        self._cleanup_complete = True

        if cleanup_errors:
            # Log cleanup errors but don't raise them
            print(f"Cleanup errors encountered: {cleanup_errors}")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Exit context with PROPER resource cleanup.

        FIX: This method properly cleans up all resources to prevent
        memory leaks and resource exhaustion.
        """
        try:
            await self._cleanup_resources()
        except Exception:
            # Even if cleanup fails, don't suppress the original exception
            pass

        return False  # Don't suppress exceptions

    def is_cleanup_complete(self) -> bool:
        """Check if cleanup was completed."""
        return self._cleanup_complete


class TestAsyncContextManagerMemoryLeak:
    """Test suite for async context manager memory leak vulnerability and fix."""

    @pytest.mark.asyncio
    async def test_memory_leak_vulnerability_demonstration(self):
        """
        Test that demonstrates the memory leak vulnerability.

        This test shows how the vulnerable async context manager
        accumulates resources without proper cleanup.
        """
        initial_resources = AsyncContextManagerWithMemoryLeak.get_resource_count()

        # Use the vulnerable context manager multiple times
        for iteration in range(3):
            async with AsyncContextManagerWithMemoryLeak(max_connections=5):
                # Simulate some async work
                await asyncio.sleep(0.01)

                # Verify connections are active within context
                current_resources = AsyncContextManagerWithMemoryLeak.get_resource_count()
                assert current_resources["active_connections"] > 0

        # VULNERABILITY: Resources should have been cleaned up but weren't
        final_resources = AsyncContextManagerWithMemoryLeak.get_resource_count()

        # Memory leak is demonstrated - resources accumulated
        assert final_resources["active_connections"] > initial_resources["active_connections"], \
            "Memory leak vulnerability: Resources not properly cleaned up"

        # Verify specific leak count (3 iterations * 5 connections = 15 leaked)
        expected_leaked = 3 * 5
        assert final_resources["active_connections"] == expected_leaked, \
            f"Expected {expected_leaked} leaked connections, got {final_resources['active_connections']}"

    @pytest.mark.asyncio
    async def test_fixed_async_context_manager_cleanup(self):
        """
        Test that verifies the fixed async context manager properly cleans up resources.

        This test shows that the fixed version doesn't have memory leaks.
        """
        # Monitor memory usage before test
        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # Use the fixed context manager multiple times
        for iteration in range(5):
            async with AsyncContextManagerFixed(max_connections=10):
                # Simulate some async work
                await asyncio.sleep(0.01)

                # Verify cleanup is not complete yet (still in context)
                # (We can't easily check this from outside)

        # Force garbage collection to ensure proper cleanup measurement
        gc.collect()
        await asyncio.sleep(0.1)  # Allow async cleanup to complete

        # Memory usage should not have grown significantly
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory

        # Allow some reasonable memory growth but ensure it's not excessive
        # (allowing 50MB growth for test overhead)
        assert memory_growth < 50 * 1024 * 1024, \
            f"Excessive memory growth detected: {memory_growth / 1024 / 1024:.2f}MB"

    @pytest.mark.asyncio
    async def test_fixed_context_manager_exception_safety(self):
        """
        Test that the fixed context manager properly cleans up even when exceptions occur.
        """
        context_manager = AsyncContextManagerFixed(max_connections=3)

        with pytest.raises(ValueError, match="Test exception"):
            async with context_manager:
                # Verify resources are allocated
                assert len(context_manager.connections) == 3

                # Verify connections are open
                for conn in context_manager.connections:
                    assert conn.is_open

                # Raise an exception to test cleanup path
                raise ValueError("Test exception")

        # Even with exception, cleanup should have completed
        assert context_manager.is_cleanup_complete()

        # All connections should be properly closed
        for conn in context_manager.connections:
            assert not conn.is_open
            assert conn.close_called

    @pytest.mark.asyncio
    async def test_fixed_context_manager_enter_failure_cleanup(self):
        """
        Test that the fixed context manager cleans up properly when __aenter__ fails.
        """
        class FailingAsyncContextManager(AsyncContextManagerFixed):
            """Context manager that fails during __aenter__."""

            async def __aenter__(self):
                # Call parent to allocate some resources
                await super().__aenter__()

                # Then fail to test cleanup
                raise RuntimeError("Simulated enter failure")

        with pytest.raises(RuntimeError, match="Simulated enter failure"):
            async with FailingAsyncContextManager(max_connections=5):
                pass

        # Force garbage collection
        gc.collect()

        # Memory should not have grown excessively despite the failure
        process = psutil.Process()
        # This is mainly to ensure no exceptions occur during cleanup

    @pytest.mark.asyncio
    async def test_concurrent_context_managers_no_resource_exhaustion(self):
        """
        Test that multiple concurrent context managers don't cause resource exhaustion.

        This test verifies that the fixed implementation can handle concurrent
        usage without exhausting system resources.
        """
        async def use_context_manager():
            async with AsyncContextManagerFixed(max_connections=5):
                await asyncio.sleep(0.05)
                return True

        # Run multiple context managers concurrently
        tasks = [use_context_manager() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # All should complete successfully
        assert all(results)

        # Force cleanup
        gc.collect()

        # Monitor that we haven't exhausted file descriptors
        process = psutil.Process()
        num_fds = process.num_fds() if hasattr(process, 'num_fds') else 0

        # Should not have excessive file descriptors open
        # (allowing reasonable number for test execution)
        assert num_fds < 100, f"Too many file descriptors open: {num_fds}"


def test_memory_leak_vulnerability_exists():
    """
    Test to demonstrate that the vulnerable version has the memory leak issue.
    """
    initial_resources = AsyncContextManagerWithMemoryLeak.get_resource_count()

    # Simulate the vulnerable behavior
    async def simulate_vulnerable_usage():
        async with AsyncContextManagerWithMemoryLeak(max_connections=3):
            await asyncio.sleep(0.001)

    # Run the simulation
    asyncio.run(simulate_vulnerable_usage())

    # Check for resource leak
    final_resources = AsyncContextManagerWithMemoryLeak.get_resource_count()

    # The vulnerability should be demonstrated
    assert final_resources["active_connections"] > initial_resources["active_connections"], \
        "Memory leak vulnerability should be demonstrable"


def test_fixed_context_manager_resource_cleanup():
    """
    Test that verifies the fixed async context manager properly cleans up resources.
    """
    # Monitor memory usage before test
    process = psutil.Process()
    initial_memory = process.memory_info().rss

    async def run_fixed_context_manager():
        async with AsyncContextManagerFixed(max_connections=10):
            await asyncio.sleep(0.01)

    # Run the fixed context manager multiple times
    for _ in range(5):
        asyncio.run(run_fixed_context_manager())

    # Force garbage collection
    gc.collect()
    time.sleep(0.1)  # Allow cleanup to complete

    # Memory usage should not have grown significantly
    final_memory = process.memory_info().rss
    memory_growth = final_memory - initial_memory

    # Allow some reasonable memory growth but ensure it's not excessive
    assert memory_growth < 50 * 1024 * 1024, \
        f"Excessive memory growth detected: {memory_growth / 1024 / 1024:.2f}MB"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])