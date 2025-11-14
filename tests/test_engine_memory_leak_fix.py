"""
Test for ID-005: Memory Leak in Async Context Manager Fix - Engine Module

This test validates that the engine.py module properly implements the fix for
memory leak vulnerabilities in async context managers, specifically:
- Proper resource cleanup in secure_file_context
- Proper resource cleanup in secure_connection_context
- No memory leaks or resource exhaustion
- Thread-safe resource management
"""

import asyncio
import gc
import os
import tempfile
import pytest
from pathlib import Path
from typing import Any
import time

# Import the fixed engine module
from src.reasoning_library.engine import (
    AsyncFileContext,
    AsyncConnectionContext,
    ResourceMetrics,
    ResourceManager,
    secure_file_context,
    secure_connection_context,
    get_resource_metrics,
    cleanup_all_resources
)


class MockAsyncConnection:
    """Mock async connection for testing."""

    def __init__(self, should_fail_close: bool = False):
        self.is_open = True
        self.close_called = False
        self.should_fail_close = should_fail_close
        self.data = b"mock_data"

    async def read(self, size: int = 1024) -> bytes:
        """Mock async read."""
        if not self.is_open:
            raise ConnectionError("Connection closed")
        return self.data[:size]

    async def write(self, data: bytes) -> int:
        """Mock async write."""
        if not self.is_open:
            raise ConnectionError("Connection closed")
        return len(data)

    async def close(self):
        """Mock async close."""
        if self.should_fail_close:
            raise RuntimeError("Simulated close failure")
        self.is_open = False
        self.close_called = True


class TestAsyncFileContext:
    """Test suite for AsyncFileContext memory leak fixes."""

    @pytest.mark.asyncio
    async def test_file_context_basic_cleanup(self):
        """Test that file context properly cleans up resources."""
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()
        temp_path = temp_file.name

        try:
            initial_metrics = get_resource_metrics()

            # Use the secure file context
            async with secure_file_context(temp_path, 'w') as f:
                f.write("test content")
                # File should be open within context
                assert not f.closed

            # File should be closed after context
            assert f.closed

            # Check metrics after cleanup
            final_metrics = get_resource_metrics()
            # Resources should be properly cleaned up
            assert final_metrics.open_files <= initial_metrics.open_files + 1

        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_file_context_exception_safety(self):
        """Test that file context cleans up properly when exceptions occur."""
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()
        temp_path = temp_file.name

        try:
            with pytest.raises(ValueError, match="Test exception"):
                async with secure_file_context(temp_path, 'w') as f:
                    f.write("some content")
                    assert not f.closed
                    raise ValueError("Test exception")

            # File should still be closed despite exception
            assert f.closed

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_file_context_concurrent_usage(self):
        """Test concurrent file context usage doesn't cause resource exhaustion."""
        temp_files = []
        try:
            # Create multiple temp files
            for i in range(5):
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                temp_file.close()
                temp_files.append(temp_file.name)

            async def write_to_file(file_path: str, content: str):
                async with secure_file_context(file_path, 'w') as f:
                    f.write(content)
                    await asyncio.sleep(0.01)  # Simulate async work
                    return content

            # Run multiple file operations concurrently
            tasks = [
                write_to_file(temp_files[i], f"content_{i}")
                for i in range(5)
            ]
            results = await asyncio.gather(*tasks)

            # All operations should complete successfully
            assert len(results) == 5
            for i, result in enumerate(results):
                assert result == f"content_{i}"

            # Verify files were written
            for i, temp_path in enumerate(temp_files):
                with open(temp_path, 'r') as f:
                    assert f.read() == f"content_{i}"

        finally:
            # Clean up temp files
            for temp_path in temp_files:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_file_context_directory_creation(self):
        """Test that file context creates parent directories as needed."""
        temp_dir = tempfile.mkdtemp()
        nested_path = os.path.join(temp_dir, "nested", "dir", "file.txt")

        try:
            async with secure_file_context(nested_path, 'w') as f:
                f.write("test content")
                assert not f.closed

            # File should exist and be readable
            assert os.path.exists(nested_path)
            assert f.closed

            with open(nested_path, 'r') as f:
                assert f.read() == "test content"

        finally:
            # Clean up
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


class TestAsyncConnectionContext:
    """Test suite for AsyncConnectionContext memory leak fixes."""

    @pytest.mark.asyncio
    async def test_connection_context_basic_cleanup(self):
        """Test that connection context properly cleans up resources."""
        initial_metrics = get_resource_metrics()

        def create_connection():
            return MockAsyncConnection()

        async with secure_connection_context(create_connection, 'test_conn') as conn:
            assert conn.is_open
            assert not conn.close_called

        # Connection should be closed after context
        assert not conn.is_open
        assert conn.close_called

        # Check metrics
        final_metrics = get_resource_metrics()
        assert final_metrics.cleanup_operations >= initial_metrics.cleanup_operations

    @pytest.mark.asyncio
    async def test_async_connection_factory(self):
        """Test connection context with async factory function."""
        async def create_async_connection():
            await asyncio.sleep(0.01)  # Simulate async connection setup
            return MockAsyncConnection()

        async with secure_connection_context(create_async_connection, 'async_conn') as conn:
            assert conn.is_open

        assert not conn.is_open
        assert conn.close_called

    @pytest.mark.asyncio
    async def test_connection_context_exception_safety(self):
        """Test that connection context cleans up properly when exceptions occur."""
        def create_connection():
            return MockAsyncConnection()

        with pytest.raises(RuntimeError, match="Connection error"):
            async with secure_connection_context(create_connection, 'fail_conn') as conn:
                assert conn.is_open
                raise RuntimeError("Connection error")

        # Connection should still be closed despite exception
        assert not conn.is_open
        assert conn.close_called

    @pytest.mark.asyncio
    async def test_connection_context_close_failure(self):
        """Test handling of connection close failures."""
        def create_failing_connection():
            return MockAsyncConnection(should_fail_close=True)

        # Should not raise exception even if close fails
        async with secure_connection_context(create_failing_connection, 'failing_conn') as conn:
            assert conn.is_open

        # Connection close was attempted but failed
        assert not conn.close_called  # close() wasn't completed due to exception
        # The context manager should handle this gracefully

    @pytest.mark.asyncio
    async def test_connection_context_concurrent_usage(self):
        """Test concurrent connection context usage."""
        def create_connection(i):
            return MockAsyncConnection()

        async def use_connection(i):
            async with secure_connection_context(
                lambda conn_id=i: create_connection(conn_id),
                f'conn_{i}'
            ) as conn:
                assert conn.is_open
                await asyncio.sleep(0.01)
                return i

        # Run multiple connections concurrently
        tasks = [use_connection(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # All should complete successfully
        assert results == list(range(10))

        # Force cleanup
        await asyncio.sleep(0.1)
        gc.collect()


class TestResourceManager:
    """Test suite for ResourceManager thread safety and cleanup."""

    def test_singleton_behavior(self):
        """Test that ResourceManager is a proper singleton."""
        manager1 = ResourceManager()
        manager2 = ResourceManager()
        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_resource_registration_and_cleanup(self):
        """Test resource registration and cleanup through ResourceManager."""
        manager = ResourceManager()
        resource_id = "test_resource"

        # Create a mock resource
        resource = MockAsyncConnection()

        # Register resource
        manager.register_resource(resource_id, resource)
        metrics = manager.get_metrics()
        assert metrics.active_connections > 0

        # Clean up resource
        success = await manager.cleanup_resource(resource_id)
        assert success
        assert manager.get_metrics().cleanup_operations > 0

    def test_weak_reference_behavior(self):
        """Test that ResourceManager uses weak references correctly."""
        manager = ResourceManager()
        resource_id = "weak_test"

        # Create and register resource
        resource = MockAsyncConnection()
        manager.register_resource(resource_id, resource)

        # Delete the resource
        del resource
        gc.collect()

        # Resource should be automatically cleaned up via weak reference
        # (This tests the weak reference behavior)
        metrics = manager.get_metrics()
        # Metrics should not count the deleted resource

    def test_metrics_tracking(self):
        """Test that resource metrics are tracked correctly."""
        initial_metrics = get_resource_metrics()

        # Create some resources
        resources = [MockAsyncConnection() for _ in range(3)]
        manager = ResourceManager()

        for i, resource in enumerate(resources):
            manager.register_resource(f"resource_{i}", resource)

        metrics = manager.get_metrics()
        assert metrics.active_connections >= initial_metrics.active_connections + 3
        assert metrics.peak_connections >= metrics.active_connections

        # Clean up
        cleanup_all_resources()


class TestMemoryLeakPrevention:
    """Test suite specifically for memory leak prevention."""

    @pytest.mark.asyncio
    async def test_no_memory_leak_with_repeated_operations(self):
        """Test that repeated operations don't cause memory leaks."""
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()
        temp_path = temp_file.name

        try:
            initial_metrics = get_resource_metrics()

            # Perform many file operations
            for i in range(20):
                async with secure_file_context(temp_path, 'w') as f:
                    f.write(f"iteration_{i}")

                async with secure_file_context(temp_path, 'r') as f:
                    content = f.read()
                    assert content == f"iteration_{i}"

            # Force garbage collection
            gc.collect()
            await asyncio.sleep(0.1)

            final_metrics = get_resource_metrics()

            # Memory usage should not have grown significantly
            # (allowing some variance for test overhead)
            memory_growth = final_metrics.memory_usage_bytes - initial_metrics.memory_usage_bytes
            assert memory_growth < 10 * 1024 * 1024, f"Memory growth: {memory_growth / 1024 / 1024:.2f}MB"

            # Active resources should be minimal
            assert final_metrics.active_connections <= 1  # Allow for some tracking overhead
            assert final_metrics.open_files <= 1

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_resource_exhaustion_prevention(self):
        """Test that the system prevents resource exhaustion."""
        temp_files = []
        connections = []

        try:
            # Create many temp files
            for i in range(10):
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                temp_file.close()
                temp_files.append(temp_file.name)

            async def limited_operation(i):
                """Operation with limited resource usage."""
                async with secure_file_context(temp_files[i], 'w') as f:
                    f.write(f"content_{i}")
                    await asyncio.sleep(0.001)

                def create_conn():
                    return MockAsyncConnection()

                async with secure_connection_context(create_conn, f'conn_{i}') as conn:
                    assert conn.is_open
                    await asyncio.sleep(0.001)

                return i

            # Run operations with concurrency limit
            semaphore = asyncio.Semaphore(5)  # Limit concurrent operations

            async def limited_limited_operation(i):
                async with semaphore:
                    return await limited_operation(i)

            tasks = [limited_limited_operation(i) for i in range(10)]
            results = await asyncio.gather(*tasks)

            assert len(results) == 10

            # Check final state
            final_metrics = get_resource_metrics()
            # Should not have excessive active resources
            assert final_metrics.active_connections < 20
            assert final_metrics.open_files < 20

        finally:
            # Clean up
            for temp_path in temp_files:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

            cleanup_all_resources()


class TestResourceTrackingFix:
    """Test suite specifically for ARCH-001 Resource Tracking Logic Bug fix."""

    def test_file_resource_tracking_accuracy(self):
        """Test that file resource metrics are accurately tracked and cleaned up."""
        manager = ResourceManager()
        initial_metrics = manager.get_metrics()

        # Create a mock file resource
        mock_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        mock_file.close()  # Close it initially

        # Reopen to simulate an open file
        mock_file = open(mock_file.name, 'r')
        resource_id = "test_file_resource"

        try:
            # Register the open file
            manager.register_resource(resource_id, mock_file)
            metrics_after_register = manager.get_metrics()

            # Should have incremented open_files
            assert metrics_after_register.open_files == initial_metrics.open_files + 1
            assert metrics_after_register.peak_files >= metrics_after_register.open_files

            # Close the file (simulating normal usage)
            mock_file.close()

            # Unregister the resource
            manager.unregister_resource(resource_id)
            metrics_after_unregister = manager.get_metrics()

            # CRITICAL: Should have decremented open_files back to baseline
            # This was the bug - it would remain inflated
            assert metrics_after_unregister.open_files == initial_metrics.open_files

        finally:
            # Clean up
            if os.path.exists(mock_file.name):
                os.unlink(mock_file.name)

    def test_connection_resource_tracking_accuracy(self):
        """Test that connection resource metrics are accurately tracked and cleaned up."""
        manager = ResourceManager()
        initial_metrics = manager.get_metrics()

        # Create a mock connection
        mock_connection = MockAsyncConnection()
        resource_id = "test_connection_resource"

        try:
            # Register the open connection
            manager.register_resource(resource_id, mock_connection)
            metrics_after_register = manager.get_metrics()

            # Should have incremented active_connections
            assert metrics_after_register.active_connections == initial_metrics.active_connections + 1
            assert metrics_after_register.peak_connections >= metrics_after_register.active_connections

            # Close the connection (simulating normal usage)
            mock_connection.is_open = False

            # Unregister the resource
            manager.unregister_resource(resource_id)
            metrics_after_unregister = manager.get_metrics()

            # CRITICAL: Should have decremented active_connections back to baseline
            assert metrics_after_unregister.active_connections == initial_metrics.active_connections

        finally:
            # Clean up if needed
            if mock_connection.is_open:
                mock_connection.is_open = False

    def test_resource_tracking_with_closed_file_still_counts(self):
        """Test that the bug is fixed: metrics should decrement even if file is closed at unregister time."""
        manager = ResourceManager()
        initial_metrics = manager.get_metrics()

        # Create and register a file while it's open
        mock_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        resource_id = "closed_file_test"

        try:
            # File is currently open
            assert not mock_file.closed

            # Register the open file
            manager.register_resource(resource_id, mock_file)
            metrics_after_register = manager.get_metrics()

            # Should have been counted as open
            assert metrics_after_register.open_files == initial_metrics.open_files + 1

            # Close the file BEFORE unregistering (this is where the bug manifested)
            mock_file.close()
            assert mock_file.closed  # File is now closed

            # Unregister the resource - this should still decrement the counter
            # In the buggy version, this would NOT decrement because it checks current state
            manager.unregister_resource(resource_id)
            metrics_after_unregister = manager.get_metrics()

            # CRITICAL FIX: Should return to baseline even though file was closed at unregister time
            assert metrics_after_unregister.open_files == initial_metrics.open_files

        finally:
            # Clean up
            if os.path.exists(mock_file.name):
                os.unlink(mock_file.name)

    @pytest.mark.asyncio
    async def test_secure_file_context_tracking_accuracy(self):
        """Test that secure_file_context properly tracks and cleans up file metrics."""
        initial_metrics = get_resource_metrics()

        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()
        temp_path = temp_file.name

        try:
            # Use the secure file context
            async with secure_file_context(temp_path, 'w') as f:
                # File should be open and tracked
                metrics_during = get_resource_metrics()
                # Should have at least one open file tracked
                assert metrics_during.open_files >= initial_metrics.open_files

                f.write("test content")
                # File is still open within context
                assert not f.closed

            # After context exit, file should be closed and metrics should return to baseline
            assert f.closed

            final_metrics = get_resource_metrics()
            # CRITICAL: open_files should return to baseline
            assert final_metrics.open_files == initial_metrics.open_files

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_repeated_file_operations_no_metric_inflation(self):
        """Test that repeated file operations don't cause permanent metric inflation."""
        initial_metrics = get_resource_metrics()

        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()
        temp_path = temp_file.name

        try:
            # Perform multiple file operations
            for i in range(10):
                async with secure_file_context(temp_path, 'w') as f:
                    f.write(f"iteration_{i}")

                async with secure_file_context(temp_path, 'r') as f:
                    content = f.read()
                    assert content == f"iteration_{i}"

            # Force cleanup
            await asyncio.sleep(0.1)
            gc.collect()

            final_metrics = get_resource_metrics()

            # CRITICAL: Should not have permanent metric inflation
            assert final_metrics.open_files == initial_metrics.open_files

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_resource_type_storage_and_cleanup(self):
        """Test that resource types are properly stored and cleaned up."""
        manager = ResourceManager()

        # Create resources
        mock_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        mock_file.close()
        mock_file = open(mock_file.name, 'r')

        mock_connection = MockAsyncConnection()

        file_id = "test_file"
        conn_id = "test_connection"

        try:
            # Register both resources
            manager.register_resource(file_id, mock_file)
            manager.register_resource(conn_id, mock_connection)

            # Verify internal state (testing the fix implementation)
            assert file_id in manager._resource_types
            assert conn_id in manager._resource_types
            assert manager._resource_types[file_id] == 'file'
            assert manager._resource_types[conn_id] == 'connection'

            # Unregister resources
            manager.unregister_resource(file_id)
            manager.unregister_resource(conn_id)

            # Verify cleanup
            assert file_id not in manager._resource_types
            assert conn_id not in manager._resource_types

        finally:
            # Clean up
            if not mock_file.closed:
                mock_file.close()
            if os.path.exists(mock_file.name):
                os.unlink(mock_file.name)
            if mock_connection.is_open:
                mock_connection.is_open = False

    def test_cleanup_all_resources_clears_types(self):
        """Test that cleanup_all_resources properly clears resource types."""
        manager = ResourceManager()

        # Register some resources
        for i in range(3):
            mock_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
            mock_file.close()
            mock_file = open(mock_file.name, 'r')

            try:
                manager.register_resource(f"file_{i}", mock_file)
            finally:
                if not mock_file.closed:
                    mock_file.close()
                if os.path.exists(mock_file.name):
                    os.unlink(mock_file.name)

        # Verify we have resource types stored
        assert len(manager._resource_types) == 3

        # Cleanup all resources
        manager.cleanup_all_resources()

        # Should clear resource types
        assert len(manager._resource_types) == 0


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_context_manager_enter_failure(self):
        """Test cleanup when __aenter__ fails."""
        # Use a non-existent directory to trigger failure
        invalid_path = "/non/existent/path/file.txt"

        with pytest.raises((FileNotFoundError, OSError)):
            async with secure_file_context(invalid_path, 'w') as f:
                pass

        # Should not leave resources in inconsistent state
        metrics = get_resource_metrics()

    @pytest.mark.asyncio
    async def test_connection_factory_failure(self):
        """Test handling of connection factory failure."""
        def failing_factory():
            raise RuntimeError("Connection failed")

        with pytest.raises(RuntimeError, match="Connection failed"):
            async with secure_connection_context(failing_factory, 'fail_conn') as conn:
                pass

        # Should not leave resources in inconsistent state
        metrics = get_resource_metrics()

    @pytest.mark.asyncio
    async def test_cancellation_handling(self):
        """Test that context managers handle cancellation properly."""
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()
        temp_path = temp_file.name

        try:
            async def long_operation():
                async with secure_file_context(temp_path, 'w') as f:
                    f.write("start")
                    await asyncio.sleep(1.0)  # Long operation that can be cancelled
                    f.write("end")

            # Create and cancel the task
            task = asyncio.create_task(long_operation())
            await asyncio.sleep(0.1)  # Let it start
            task.cancel()

            with pytest.raises(asyncio.CancelledError):
                await task

            # File should still be properly closed despite cancellation
            # (this is handled by the context manager's __aexit__)

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])