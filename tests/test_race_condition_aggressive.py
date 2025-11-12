#!/usr/bin/env python3
"""
AGGRESSIVE RACE CONDITION TEST - Demonstrating Actual Thread Safety Violations

This test directly demonstrates the specific race condition vulnerabilities
in the reasoning_library core module by accessing unsynchronized shared state.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import threading
import time
import weakref
from concurrent.futures import ThreadPoolExecutor
from reasoning_library.core import (
    _math_detection_cache,
    _function_source_cache,
    ENHANCED_TOOL_REGISTRY,
    TOOL_REGISTRY,
    _get_math_detection_cached,
    _get_function_source_cached,
    tool_spec
)


def create_test_function(name: str):
    """Create a unique test function."""
    def func():
        return f"result_{name}"
    func.__name__ = name
    func.__doc__ = f"Test function {name} for confidence calculation based on pattern quality."
    return func


def test_direct_race_condition():
    """Test that directly exploits race condition in _get_math_detection_cached."""
    print("\n🔍 Testing direct race condition in _math_detection_cached...")

    # Clear cache
    _math_detection_cache.clear()

    errors = []

    def race_worker(worker_id):
        """Worker that triggers race condition."""
        try:
            # Create functions that will cause cache eviction
            functions = [create_test_function(f"race_worker_{worker_id}_{i}") for i in range(100)]

            for i, func in enumerate(functions):
                # This function accesses shared state without locking
                result = _get_math_detection_cached(func)

                # Rapid concurrent access can cause race conditions
                if i % 10 == 0:
                    # Access again to hit cache
                    result2 = _get_math_detection_cached(func)
                    if result != result2:
                        errors.append(f"Worker {worker_id}: Inconsistent results for function {i}")
        except Exception as e:
            errors.append(f"Worker {worker_id} crashed: {e}")

    # Run multiple workers to create race condition
    threads = []
    for i in range(20):
        t = threading.Thread(target=race_worker, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print(f"  Race condition test completed. Errors: {len(errors)}")
    return len(errors) > 0


def test_registry_race_condition():
    """Test race condition in registry access."""
    print("\n🔍 Testing registry race condition...")

    # Clear registries
    ENHANCED_TOOL_REGISTRY.clear()
    TOOL_REGISTRY.clear()

    errors = []

    @tool_spec
    def base_function():
        """Base test function."""
        return "test"

    def registry_writer(worker_id):
        """Writer thread that adds to registry."""
        try:
            for i in range(50):
                @tool_spec
                def writer_func():
                    """Writer function."""
                    return f"writer_{worker_id}_{i}"
                # Small delay to increase race condition likelihood
                time.sleep(0.001)
        except Exception as e:
            errors.append(f"Registry writer {worker_id} error: {e}")

    def registry_reader(worker_id):
        """Reader thread that reads from registry."""
        try:
            for i in range(100):
                # Reading registry while it's being modified - race condition
                enhanced_size = len(ENHANCED_TOOL_REGISTRY)
                tool_size = len(TOOL_REGISTRY)

                # Check for inconsistency
                if enhanced_size != tool_size:
                    errors.append(f"Reader {worker_id}: Registry size mismatch: {enhanced_size} vs {tool_size}")

                time.sleep(0.001)
        except Exception as e:
            errors.append(f"Registry reader {worker_id} error: {e}")

    # Run concurrent readers and writers
    threads = []

    # Start writers
    for i in range(5):
        t = threading.Thread(target=registry_writer, args=(i,))
        threads.append(t)
        t.start()

    # Start readers
    for i in range(10):
        t = threading.Thread(target=registry_reader, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print(f"  Registry race condition test completed. Errors: {len(errors)}")
    return len(errors) > 0


def test_weakref_race_condition():
    """Test race condition in WeakKeyDictionary access."""
    print("\n🔍 testing WeakKeyDictionary race condition...")

    # Clear cache
    _function_source_cache.clear()

    errors = []

    def weakref_worker(worker_id):
        """Worker that accesses WeakKeyDictionary concurrently."""
        try:
            functions = [create_test_function(f"weakref_worker_{worker_id}_{i}") for i in range(50)]

            for i, func in enumerate(functions):
                # Direct access to WeakKeyDictionary - race condition
                source1 = _get_function_source_cached(func)
                source2 = _get_function_source_cached(func)

                if source1 != source2:
                    errors.append(f"Weakref worker {worker_id}: Inconsistent source code")

                # Check cache integrity
                try:
                    size = len(_function_source_cache)
                    if size < 0:
                        errors.append(f"Weakref worker {worker_id}: Negative cache size: {size}")
                except Exception as e:
                    errors.append(f"Weakref worker {worker_id}: Cache size error: {e}")
        except Exception as e:
            errors.append(f"Weakref worker {worker_id} crashed: {e}")

    # Run many workers to increase race condition probability
    threads = []
    for i in range(15):
        t = threading.Thread(target=weakref_worker, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print(f"  WeakKeyDictionary race condition test completed. Errors: {len(errors)}")
    return len(errors) > 0


def main():
    """Run aggressive race condition tests."""
    print("=" * 80)
    print("🚨 AGGRESSIVE RACE CONDITION VULNERABILITY TEST 🚨")
    print("=" * 80)

    race_detected = False

    # Test 1: Direct race condition in _get_math_detection_cached
    if test_direct_race_condition():
        print("❌ Race condition detected in _get_math_detection_cached")
        race_detected = True

    # Test 2: Registry race condition
    if test_registry_race_condition():
        print("❌ Race condition detected in registry access")
        race_detected = True

    # Test 3: WeakKeyDictionary race condition
    if test_weakref_race_condition():
        print("❌ Race condition detected in WeakKeyDictionary access")
        race_detected = True

    print("\n" + "=" * 80)
    if race_detected:
        print("❌ RACE CONDITIONS CONFIRMED - Vulnerabilities exist!")
        print("❌ The reasoning_library has CRITICAL thread safety vulnerabilities!")
        return False
    else:
        print("⚠️ No race conditions detected in this run")
        print("⚠️ But vulnerabilities may still exist in the code")
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)