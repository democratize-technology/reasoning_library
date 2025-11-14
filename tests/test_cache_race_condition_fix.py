#!/usr/bin/env python3
"""
Comprehensive tests for cache management race condition fixes.

Tests verify that the atomic operations implemented in core.py eliminate
race conditions in cache management under concurrent load.
"""

import threading
import time
import concurrent.futures
import pytest
from unittest.mock import patch

from reasoning_library.core import (
    _math_detection_cache, _function_source_cache, _cache_lock, MAX_CACHE_SIZE,
    CACHE_EVICTION_FRACTION, ENHANCED_TOOL_REGISTRY, TOOL_REGISTRY, _registry_lock,
    MAX_REGISTRY_SIZE, REGISTRY_EVICTION_FRACTION,
    _get_math_detection_cached, _get_function_source_cached,
    _manage_registry_size, clear_performance_caches
)


class TestCacheRaceConditionFixes:
    """Test suite to verify race condition fixes in cache management."""

    def setup_method(self):
        """Clear all caches and registries before each test."""
        clear_performance_caches()

    def teardown_method(self):
        """Clean up after each test."""
        clear_performance_caches()

    def test_atomic_cache_operations_under_concurrent_access(self):
        """Test that cache operations remain atomic under high concurrent load."""
        errors = []
        results = []

        def create_test_function(worker_id, func_id):
            """Create a unique test function for each worker."""
            def test_func():
                return f"worker_{worker_id}_func_{func_id}"
            test_func.__name__ = f"test_func_{worker_id}_{func_id}"
            test_func.__module__ = "test_module"
            test_func.__qualname__ = f"Test.test_func_{worker_id}_{func_id}"
            test_func.__doc__ = f"Test function from worker {worker_id}, function {func_id}"
            return test_func

        def cache_worker(worker_id):
            """Worker that performs cache operations concurrently."""
            try:
                for i in range(50):
                    func = create_test_function(worker_id, i)
                    result = _get_math_detection_cached(func)

                    # Verify result integrity
                    assert isinstance(result, tuple), f"Result should be tuple, got {type(result)}"
                    assert len(result) == 3, f"Result should have 3 elements, got {len(result)}"

                    results.append((worker_id, i, result))

                    # Test function source caching as well
                    source_result = _get_function_source_cached(func)
                    assert isinstance(source_result, str), f"Source result should be string"

            except Exception as e:
                errors.append(f"Cache worker {worker_id}: {e}")

        # Run many threads concurrently
        threads = []
        for i in range(20):
            thread = threading.Thread(target=cache_worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify no errors occurred
        assert len(errors) == 0, f"Concurrent cache access errors: {errors}"

        # Verify all operations completed
        expected_operations = 20 * 50  # 20 workers * 50 operations each
        assert len(results) == expected_operations, f"Expected {expected_operations} results, got {len(results)}"

        # Verify cache integrity
        with _cache_lock:
            for key, value in _math_detection_cache.items():
                assert isinstance(value, tuple) and len(value) == 3, \
                    f"Cache corruption detected: key={key}, value={value}"

    def test_atomic_cache_eviction_under_stress(self):
        """Test that cache eviction works atomically under stress."""
        errors = []
        cache_sizes = []

        def eviction_stress_worker(worker_id):
            """Worker that stresses cache eviction."""
            try:
                for i in range(100):
                    def test_func():
                        return f"stress_worker_{worker_id}_func_{i}"
                    test_func.__name__ = f"stress_func_{worker_id}_{i}"
                    test_func.__module__ = "stress_module"
                    test_func.__qualname__ = f"Stress.test_func_{worker_id}_{i}"
                    test_func.__doc__ = f"Stress test function {worker_id}-{i}"

                    # This should trigger cache operations and potential eviction
                    result = _get_math_detection_cached(test_func)

                    # Track cache sizes
                    with _cache_lock:
                        cache_sizes.append(len(_math_detection_cache))

                        # Verify cache never exceeds reasonable bounds
                        assert len(_math_detection_cache) <= MAX_CACHE_SIZE * 1.5, \
                            f"Cache exceeded bounds: {len(_math_detection_cache)}"

            except Exception as e:
                errors.append(f"Eviction stress worker {worker_id}: {e}")

        # Run many threads to stress eviction logic
        threads = []
        for i in range(50):
            thread = threading.Thread(target=eviction_stress_worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify no errors occurred
        assert len(errors) == 0, f"Eviction stress errors: {errors}"

        # Verify cache never exceeded reasonable maximum
        max_cache_size = max(cache_sizes) if cache_sizes else 0
        assert max_cache_size <= MAX_CACHE_SIZE * 1.5, \
            f"Cache exceeded maximum during stress: {max_cache_size}"

    def test_atomic_registry_operations_under_concurrent_access(self):
        """Test that registry operations remain atomic under concurrent load."""
        errors = []
        registry_sizes = []

        def registry_stress_worker(worker_id):
            """Worker that stresses registry operations."""
            try:
                for i in range(50):
                    # Add entries to trigger size management
                    with _registry_lock:
                        ENHANCED_TOOL_REGISTRY.append(f"worker_{worker_id}_enhanced_{i}")
                        TOOL_REGISTRY.append(f"worker_{worker_id}_tool_{i}")

                    # Trigger registry management (should be thread-safe)
                    _manage_registry_size()

                    # Track registry sizes
                    with _registry_lock:
                        registry_sizes.append((
                            len(ENHANCED_TOOL_REGISTRY),
                            len(TOOL_REGISTRY)
                        ))

                        # Verify registries stay within reasonable bounds
                        assert len(ENHANCED_TOOL_REGISTRY) <= MAX_REGISTRY_SIZE * 1.5, \
                            f"Enhanced registry too large: {len(ENHANCED_TOOL_REGISTRY)}"
                        assert len(TOOL_REGISTRY) <= MAX_REGISTRY_SIZE * 1.5, \
                            f"Tool registry too large: {len(TOOL_REGISTRY)}"

            except Exception as e:
                errors.append(f"Registry stress worker {worker_id}: {e}")

        # Run many threads
        threads = []
        for i in range(30):
            thread = threading.Thread(target=registry_stress_worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify no errors occurred
        assert len(errors) == 0, f"Registry stress errors: {errors}"

        # Verify registries never exceeded reasonable maximum
        if registry_sizes:
            max_enhanced = max(size[0] for size in registry_sizes)
            max_tool = max(size[1] for size in registry_sizes)
            assert max_enhanced <= MAX_REGISTRY_SIZE * 1.5, \
                f"Enhanced registry exceeded max: {max_enhanced}"
            assert max_tool <= MAX_REGISTRY_SIZE * 1.5, \
                f"Tool registry exceeded max: {max_tool}"

    def test_concurrent_cache_clear_operations(self):
        """Test that cache clearing works correctly with concurrent access."""
        errors = []
        clear_count = 0
        access_count = 0

        def clear_worker():
            """Worker that clears caches periodically."""
            nonlocal clear_count
            try:
                for i in range(20):
                    clear_performance_caches()
                    clear_count += 1
                    time.sleep(0.001)  # Small delay
            except Exception as e:
                errors.append(f"Clear worker error: {e}")

        def access_worker(worker_id):
            """Worker that accesses caches while clearing occurs."""
            nonlocal access_count
            try:
                for i in range(100):
                    def test_func():
                        return f"concurrent_func_{worker_id}_{i}"
                    test_func.__name__ = f"concurrent_func_{worker_id}_{i}"
                    test_func.__module__ = "concurrent_module"
                    test_func.__qualname__ = f"Concurrent.test_func_{worker_id}_{i}"
                    test_func.__doc__ = f"Concurrent test function {worker_id}-{i}"

                    result = _get_math_detection_cached(test_func)
                    assert isinstance(result, tuple) and len(result) == 3
                    access_count += 1

            except Exception as e:
                errors.append(f"Access worker {worker_id} error: {e}")

        # Start cache clearing thread
        clear_thread = threading.Thread(target=clear_worker)
        clear_thread.start()

        # Start multiple access threads
        access_threads = []
        for i in range(10):
            thread = threading.Thread(target=access_worker, args=(i,))
            access_threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        clear_thread.join()
        for thread in access_threads:
            thread.join()

        # Verify no errors occurred
        assert len(errors) == 0, f"Concurrent clear/access errors: {errors}"

        # Verify operations completed
        assert clear_count > 0, "No clear operations occurred"
        assert access_count > 0, "No access operations occurred"

    def test_memory_safety_under_extreme_concurrency(self):
        """Test memory safety and data integrity under extreme concurrency."""
        errors = []
        operation_counts = {'cache': 0, 'registry': 0, 'clear': 0}

        def extreme_worker(worker_id):
            """Worker that performs extreme concurrent operations."""
            try:
                for i in range(200):
                    # Cache operations
                    def test_func():
                        return f"extreme_func_{worker_id}_{i}"
                    test_func.__name__ = f"extreme_func_{worker_id}_{i}"
                    test_func.__module__ = "extreme_module"
                    test_func.__qualname__ = f"Extreme.test_func_{worker_id}_{i}"
                    test_func.__doc__ = f"Extreme test function {worker_id}-{i}"

                    _get_math_detection_cached(test_func)
                    _get_function_source_cached(test_func)
                    operation_counts['cache'] += 1

                    # Registry operations
                    with _registry_lock:
                        ENHANCED_TOOL_REGISTRY.append(f"extreme_enhanced_{worker_id}_{i}")
                        TOOL_REGISTRY.append(f"extreme_tool_{worker_id}_{i}")

                    _manage_registry_size()
                    operation_counts['registry'] += 1

                    # Clear operations
                    if i % 50 == 0:
                        clear_performance_caches()
                        operation_counts['clear'] += 1

                    # Verify integrity periodically
                    if i % 25 == 0:
                        with _cache_lock:
                            for key, value in _math_detection_cache.items():
                                assert isinstance(value, tuple) and len(value) == 3, \
                                    f"Memory corruption: key={key}, value={value}"

                        with _registry_lock:
                            assert len(ENHANCED_TOOL_REGISTRY) <= MAX_REGISTRY_SIZE * 2, \
                                f"Memory leak in enhanced registry: {len(ENHANCED_TOOL_REGISTRY)}"
                            assert len(TOOL_REGISTRY) <= MAX_REGISTRY_SIZE * 2, \
                                f"Memory leak in tool registry: {len(TOOL_REGISTRY)}"

            except Exception as e:
                errors.append(f"Extreme worker {worker_id} error: {e}")

        # Run extreme concurrency test
        threads = []
        for i in range(40):
            thread = threading.Thread(target=extreme_worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify no errors occurred
        assert len(errors) == 0, f"Extreme concurrency errors: {errors}"

        # Verify significant operation counts
        assert operation_counts['cache'] > 0, "No cache operations in extreme test"
        assert operation_counts['registry'] > 0, "No registry operations in extreme test"
        assert operation_counts['clear'] > 0, "No clear operations in extreme test"

        # Final integrity check
        with _cache_lock:
            for key, value in _math_detection_cache.items():
                assert isinstance(value, tuple) and len(value) == 3, \
                    f"Final memory corruption: key={key}, value={value}"

        with _registry_lock:
            assert len(ENHANCED_TOOL_REGISTRY) <= MAX_REGISTRY_SIZE * 2, \
                f"Final enhanced registry size: {len(ENHANCED_TOOL_REGISTRY)}"
            assert len(TOOL_REGISTRY) <= MAX_REGISTRY_SIZE * 2, \
                f"Final tool registry size: {len(TOOL_REGISTRY)}"

    @pytest.mark.slow
    def test_deterministic_cache_behavior_under_concurrency(self):
        """Test that cache behavior remains deterministic under concurrent access."""
        # Create identical functions
        def create_identical_function(name_suffix):
            def test_func():
                return "identical_function"
            test_func.__name__ = f"identical_func_{name_suffix}"
            test_func.__module__ = "deterministic_test"
            test_func.__qualname__ = f"DeterministicTest.identical_func_{name_suffix}"
            test_func.__doc__ = "Identical test function for deterministic behavior"
            return test_func

        # Create identical functions that should hash to same cache key
        identical_funcs = [create_identical_function(i) for i in range(10)]

        results = {}

        def deterministic_worker(worker_id):
            """Worker that accesses identical functions."""
            try:
                for i, func in enumerate(identical_funcs):
                    # Multiple workers accessing same functions should get same results
                    result = _get_math_detection_cached(func)

                    # Store results for later comparison
                    func_key = id(func)
                    if func_key not in results:
                        results[func_key] = []
                    results[func_key].append((worker_id, result))

                    # Verify all results are valid
                    assert isinstance(result, tuple) and len(result) == 3

            except Exception as e:
                raise AssertionError(f"Deterministic worker {worker_id} error: {e}")

        # Run multiple workers accessing identical functions
        threads = []
        for i in range(5):
            thread = threading.Thread(target=deterministic_worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify deterministic behavior
        for func_key, func_results in results.items():
            # All workers should get identical results for the same function
            unique_results = set(str(result) for _, result in func_results)
            assert len(unique_results) == 1, \
                f"Non-deterministic results for function {func_key}: {unique_results}"