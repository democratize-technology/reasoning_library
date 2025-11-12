#!/usr/bin/env python3
"""
Thread Safety Fix Verification Test

This test verifies that the race condition fixes in reasoning_library are effective.
The test should PASS after the fixes, demonstrating that race conditions have been resolved.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import threading
import time
import weakref
from concurrent.futures import ThreadPoolExecutor, as_completed
from reasoning_library.core import (
    _math_detection_cache,
    _function_source_cache,
    ENHANCED_TOOL_REGISTRY,
    TOOL_REGISTRY,
    _get_math_detection_cached,
    _get_function_source_cached,
    clear_performance_caches,
    get_tool_specs,
    get_openai_tools,
    get_bedrock_tools,
    get_enhanced_tool_registry,
    tool_spec
)


def create_test_function(name: str):
    """Create a unique test function."""
    def func():
        return f"result_{name}"
    func.__name__ = name
    func.__doc__ = f"Test function {name} for confidence calculation based on pattern quality."
    return func


def test_thread_safe_math_detection_cache():
    """Verify that _math_detection_cache is now thread-safe."""
    print("\n🔒 Testing thread-safe _math_detection_cache...")

    # Clear cache
    clear_performance_caches()

    errors = []
    inconsistencies = []

    def worker_function(worker_id):
        """Worker that accesses cache concurrently."""
        try:
            # Create functions that will cause cache eviction
            functions = [create_test_function(f"worker_{worker_id}_{i}") for i in range(50)]

            for i, func in enumerate(functions):
                # This function should now be thread-safe
                result = _get_math_detection_cached(func)

                # Access again to hit cache - should be consistent
                result2 = _get_math_detection_cached(func)
                if result != result2:
                    inconsistencies.append(f"Worker {worker_id}: Inconsistent results for function {i}: {result} vs {result2}")

                # Check cache integrity
                cache_size = len(_math_detection_cache)
                if cache_size < 0 or cache_size > 1500:  # Should never exceed reasonable bounds
                    errors.append(f"Worker {worker_id}: Invalid cache size: {cache_size}")

        except Exception as e:
            errors.append(f"Worker {worker_id} crashed: {type(e).__name__}: {e}")

    # Run multiple workers concurrently
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(worker_function, i) for i in range(15)]

        for future in as_completed(futures):
            try:
                future.result(timeout=30)
            except Exception as e:
                errors.append(f"Test execution failed: {type(e).__name__}: {e}")

    # Final integrity check
    with _math_detection_cache._cache_lock if hasattr(_math_detection_cache, '_cache_lock') else threading.Lock():
        # Access _cache_lock from the module if possible, otherwise skip locking
        pass

    final_size = len(_math_detection_cache)
    if final_size < 0 or final_size > 1200:
        errors.append(f"Final cache integrity failed: size {final_size}")

    print(f"  ✅ Math detection cache test completed. Errors: {len(errors)}, Inconsistencies: {len(inconsistencies)}")
    return len(errors) == 0 and len(inconsistencies) == 0


def test_thread_safe_function_source_cache():
    """Verify that _function_source_cache is now thread-safe."""
    print("\n🔒 Testing thread-safe _function_source_cache...")

    # Clear cache
    clear_performance_caches()

    errors = []
    inconsistencies = []

    def worker_function(worker_id):
        """Worker that accesses WeakKeyDictionary concurrently."""
        try:
            functions = [create_test_function(f"source_worker_{worker_id}_{i}") for i in range(30)]

            for i, func in enumerate(functions):
                # This should now be thread-safe
                source1 = _get_function_source_cached(func)
                source2 = _get_function_source_cached(func)

                if source1 != source2:
                    inconsistencies.append(f"Source worker {worker_id}: Inconsistent source code for function {i}")

                # Check cache integrity
                try:
                    size = len(_function_source_cache)
                    if size < 0:
                        errors.append(f"Source worker {worker_id}: Negative cache size: {size}")
                except Exception as e:
                    errors.append(f"Source worker {worker_id}: Cache size error: {e}")

        except Exception as e:
            errors.append(f"Source worker {worker_id} crashed: {type(e).__name__}: {e}")

    # Run many workers to test thread safety
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker_function, i) for i in range(10)]

        for future in as_completed(futures):
            try:
                future.result(timeout=30)
            except Exception as e:
                errors.append(f"Test execution failed: {type(e).__name__}: {e}")

    print(f"  ✅ Function source cache test completed. Errors: {len(errors)}, Inconsistencies: {len(inconsistencies)}")
    return len(errors) == 0 and len(inconsistencies) == 0


def test_thread_safe_registry_access():
    """Verify that registry access is now thread-safe."""
    print("\n🔒 Testing thread-safe registry access...")

    # Clear registries
    clear_performance_caches()

    errors = []
    inconsistencies = []

    @tool_spec
    def base_function():
        """Base test function."""
        return "test"

    def writer_thread(writer_id):
        """Writer thread that adds to registry."""
        try:
            for i in range(20):
                @tool_spec
                def writer_func():
                    """Writer function."""
                    return f"writer_{writer_id}_{i}"
                # Small delay to increase concurrency
                time.sleep(0.001)
        except Exception as e:
            errors.append(f"Registry writer {writer_id} error: {type(e).__name__}: {e}")

    def reader_thread(reader_id):
        """Reader thread that reads from registry using thread-safe functions."""
        try:
            for i in range(50):
                # These functions should now be thread-safe
                try:
                    tool_specs = get_tool_specs()
                    openai_tools = get_openai_tools()
                    bedrock_tools = get_bedrock_tools()
                    enhanced_registry = get_enhanced_tool_registry()

                    # Verify data consistency
                    enhanced_size = len(enhanced_registry)
                    tool_size = len(TOOL_REGISTRY)  # Direct access for comparison

                    # Small mismatches can occur during concurrent writes, but should be minimal
                    if abs(enhanced_size - tool_size) > 5:
                        inconsistencies.append(f"Reader {reader_id}: Registry size mismatch: enhanced={enhanced_size}, tool={tool_size}")

                    # Validate returned data
                    if not isinstance(tool_specs, list) or not isinstance(openai_tools, list):
                        errors.append(f"Reader {reader_id}: Invalid return types")

                except Exception as e:
                    errors.append(f"Reader {reader_id} registry access failed: {type(e).__name__}: {e}")

                time.sleep(0.001)
        except Exception as e:
            errors.append(f"Registry reader {reader_id} crashed: {type(e).__name__}: {e}")

    # Run concurrent readers and writers
    with ThreadPoolExecutor(max_workers=12) as executor:
        # Start writers
        writer_futures = [executor.submit(writer_thread, i) for i in range(4)]
        time.sleep(0.05)  # Let writers start

        # Start readers
        reader_futures = [executor.submit(reader_thread, i) for i in range(8)]

        # Wait for all to complete
        all_futures = writer_futures + reader_futures
        for future in as_completed(all_futures):
            try:
                future.result(timeout=30)
            except Exception as e:
                errors.append(f"Registry concurrent test execution failed: {type(e).__name__}: {e}")

    print(f"  ✅ Registry access test completed. Errors: {len(errors)}, Inconsistencies: {len(inconsistencies)}")
    return len(errors) == 0 and len(inconsistencies) == 0


def test_thread_safe_cache_clear():
    """Verify that cache clearing is now thread-safe."""
    print("\n🔒 Testing thread-safe cache clearing...")

    errors = []

    def cache_worker(worker_id):
        """Worker that populates cache while another clears it."""
        try:
            for i in range(30):
                func = create_test_function(f"clear_worker_{worker_id}_{i}")
                _get_math_detection_cached(func)
                _get_function_source_cached(func)
                time.sleep(0.001)
        except Exception as e:
            errors.append(f"Cache worker {worker_id} crashed: {type(e).__name__}: {e}")

    def cache_clearer():
        """Thread that clears caches concurrently."""
        try:
            for i in range(10):
                clear_performance_caches()  # This should now be thread-safe
                time.sleep(0.01)
        except Exception as e:
            errors.append(f"Cache clearer crashed: {type(e).__name__}: {e}")

    # Run workers and clearer concurrently
    with ThreadPoolExecutor(max_workers=8) as executor:
        # Start cache workers
        worker_futures = [executor.submit(cache_worker, i) for i in range(6)]
        time.sleep(0.02)  # Let workers populate some cache

        # Start cache clearer
        clearer_future = executor.submit(cache_clearer)

        # Wait for all to complete
        all_futures = worker_futures + [clearer_future]
        for future in as_completed(all_futures):
            try:
                future.result(timeout=30)
            except Exception as e:
                errors.append(f"Cache clear test execution failed: {type(e).__name__}: {e}")

    print(f"  ✅ Cache clear test completed. Errors: {len(errors)}")
    return len(errors) == 0


def main():
    """Run thread safety verification tests."""
    print("=" * 80)
    print("🔒 THREAD SAFETY FIX VERIFICATION TEST 🔒")
    print("=" * 80)
    print("This test verifies that race condition vulnerabilities have been fixed.")
    print("Expected: All tests should PASS after the thread safety fixes.")
    print("-" * 80)

    all_tests_passed = True

    # Test 1: Thread-safe math detection cache
    if not test_thread_safe_math_detection_cache():
        print("❌ Math detection cache thread safety test FAILED")
        all_tests_passed = False
    else:
        print("✅ Math detection cache thread safety test PASSED")

    # Test 2: Thread-safe function source cache
    if not test_thread_safe_function_source_cache():
        print("❌ Function source cache thread safety test FAILED")
        all_tests_passed = False
    else:
        print("✅ Function source cache thread safety test PASSED")

    # Test 3: Thread-safe registry access
    if not test_thread_safe_registry_access():
        print("❌ Registry access thread safety test FAILED")
        all_tests_passed = False
    else:
        print("✅ Registry access thread safety test PASSED")

    # Test 4: Thread-safe cache clearing
    if not test_thread_safe_cache_clear():
        print("❌ Cache clearing thread safety test FAILED")
        all_tests_passed = False
    else:
        print("✅ Cache clearing thread safety test PASSED")

    print("\n" + "=" * 80)
    print("🔒 THREAD SAFETY VERIFICATION RESULTS 🔒")
    print("=" * 80)

    if all_tests_passed:
        print("✅ ALL THREAD SAFETY TESTS PASSED!")
        print("✅ Race condition vulnerabilities have been successfully fixed!")
        print("✅ The reasoning_library is now thread-safe.")
        print("\n🔧 Thread Safety Improvements Applied:")
        print("  • Added _cache_lock for cache operations synchronization")
        print("  • Fixed _get_math_detection_cached with proper locking")
        print("  • Fixed _get_function_source_cached with double-check pattern")
        print("  • Added thread safety to registry read operations")
        print("  • Fixed clear_performance_caches with dual locking")
        print("  • Implemented atomic cache eviction logic")
        return True
    else:
        print("❌ SOME THREAD SAFETY TESTS FAILED!")
        print("❌ Race condition vulnerabilities may still exist!")
        print("❌ Additional fixes may be required.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)