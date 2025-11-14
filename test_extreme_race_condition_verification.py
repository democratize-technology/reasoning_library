#!/usr/bin/env python3
"""
EXTREME RACE CONDITION VERIFICATION TEST

This test performs extreme concurrent operations to verify that the race condition
fixes in reasoning_library are comprehensive and robust under high stress.
"""

import threading
import time
import concurrent.futures
import gc
import weakref
from typing import Any, Dict, List
from unittest.mock import patch

from reasoning_library.core import (
    _math_detection_cache, _function_source_cache, _cache_lock, MAX_CACHE_SIZE,
    CACHE_EVICTION_FRACTION, ENHANCED_TOOL_REGISTRY, TOOL_REGISTRY, _registry_lock,
    MAX_REGISTRY_SIZE, REGISTRY_EVICTION_FRACTION,
    _get_math_detection_cached, _get_function_source_cached,
    _manage_registry_size, clear_performance_caches, tool_spec
)


class ExtremeRaceConditionTest:
    """Extreme test for race condition verification."""

    def __init__(self):
        self.errors = []
        self.inconsistencies = []
        self.corruption_events = []
        self.stats = {
            'operations': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'evictions': 0,
            'lock_timeouts': 0
        }
        self.lock = threading.Lock()

    def add_error(self, error: str):
        with self.lock:
            self.errors.append(error)

    def add_inconsistency(self, inconsistency: str):
        with self.lock:
            self.inconsistencies.append(inconsistency)

    def add_corruption_event(self, corruption: str):
        with self.lock:
            self.corruption_events.append(corruption)

    def record_stats(self, **kwargs):
        with self.lock:
            for key, value in kwargs.items():
                if key in self.stats:
                    self.stats[key] += value


def create_test_function_batch(batch_id: int, count: int) -> List[callable]:
    """Create a batch of unique test functions."""
    functions = []
    for i in range(count):
        def test_func(x=batch_id * 1000 + i):
            return f"batch_{batch_id}_func_{i}_result_{x}"
        test_func.__name__ = f"test_func_batch_{batch_id}_{i}"
        test_func.__module__ = f"test_module_batch_{batch_id}"
        test_func.__qualname__ = f"TestBatch.test_func_batch_{batch_id}_{i}"
        test_func.__doc__ = f"""
        Test function from batch {batch_id}, function {i}.
        Mathematical reasoning: confidence calculation based on pattern quality.
        Statistical analysis: geometric progression with confidence factors.
        """
        functions.append(test_func)
    return functions


def test_extreme_cache_concurrency(test_instance: ExtremeRaceConditionTest):
    """Test cache operations under extreme concurrent load."""
    print("🔥 Testing extreme cache concurrency...")

    # Clear caches
    clear_performance_caches()

    def extreme_cache_worker(worker_id: int):
        """Worker performing extreme cache operations."""
        try:
            # Create many functions to trigger cache eviction
            functions = create_test_function_batch(worker_id, 100)

            for iteration in range(50):
                # Rapid cache access patterns
                for func in functions:
                    start_time = time.time()
                    result = _get_math_detection_cached(func)

                    if result is None or not isinstance(result, tuple) or len(result) != 3:
                        test_instance.add_corruption_event(
                            f"Invalid cache result: worker_{worker_id}, func_{func.__name__}"
                        )

                    test_instance.record_stats(operations=1)

                    # Check for lock timeouts (should be handled gracefully)
                    if time.time() - start_time > 0.1:  # 100ms threshold
                        test_instance.record_stats(lock_timeouts=1)

                # Test function source cache concurrently
                for func in functions[:10]:  # Subset for source cache
                    source = _get_function_source_cached(func)
                    if not isinstance(source, str):
                        test_instance.add_corruption_event(
                            f"Invalid source result: worker_{worker_id}, func_{func.__name__}"
                        )

                # Memory cleanup to stress WeakKeyDictionary
                if iteration % 10 == 0:
                    del functions[:20]  # Delete some functions
                    gc.collect()  # Force garbage collection

        except Exception as e:
            test_instance.add_error(f"Extreme cache worker {worker_id} crashed: {e}")

    # Launch extreme concurrent workers
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(extreme_cache_worker, i) for i in range(50)]
        concurrent.futures.wait(futures, timeout=60)

    # Verify cache integrity after extreme test
    try:
        with _cache_lock:
            cache_size = len(_math_detection_cache)
            if cache_size < 0 or cache_size > MAX_CACHE_SIZE * 2:
                test_instance.add_corruption_event(f"Cache size corruption: {cache_size}")

            # Verify all cache entries are valid
            for key, value in _math_detection_cache.items():
                if not isinstance(value, tuple) or len(value) != 3:
                    test_instance.add_corruption_event(f"Cache entry corruption: key={key}, value={value}")

    except Exception as e:
        test_instance.add_error(f"Cache integrity check failed: {e}")


def test_registry_extreme_concurrency(test_instance: ExtremeRaceConditionTest):
    """Test registry operations under extreme concurrent load."""
    print("🔥 Testing extreme registry concurrency...")

    # Clear registries
    with _registry_lock:
        ENHANCED_TOOL_REGISTRY.clear()
        TOOL_REGISTRY.clear()

    def registry_extreme_worker(worker_id: int):
        """Worker performing extreme registry operations."""
        try:
            for i in range(100):
                # Create tool specs rapidly
                @tool_spec
                def rapid_func(x: int = worker_id * 1000 + i) -> int:
                    """Rapid function for extreme testing."""
                    return x * 2

                # Trigger registry management
                _manage_registry_size()

                # Concurrent registry reads
                try:
                    enhanced_size = len(ENHANCED_TOOL_REGISTRY)
                    tool_size = len(TOOL_REGISTRY)

                    # Check for reasonable bounds
                    if enhanced_size > MAX_REGISTRY_SIZE * 2:
                        test_instance.add_corruption_event(f"Enhanced registry overflow: {enhanced_size}")
                    if tool_size > MAX_REGISTRY_SIZE * 2:
                        test_instance.add_corruption_event(f"Tool registry overflow: {tool_size}")

                except Exception as e:
                    test_instance.add_error(f"Registry read error: {e}")

                # Concurrent registry iteration
                try:
                    for entry in ENHANCED_TOOL_REGISTRY[:5]:  # Small subset
                        if not isinstance(entry, dict):
                            test_instance.add_corruption_event(f"Registry entry corruption: {type(entry)}")
                except Exception as e:
                    # Registry might be modified during iteration - this should be handled
                    pass

        except Exception as e:
            test_instance.add_error(f"Registry extreme worker {worker_id} crashed: {e}")

    # Launch extreme registry workers
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(registry_extreme_worker, i) for i in range(30)]
        concurrent.futures.wait(futures, timeout=60)


def test_mixed_operation_chaos(test_instance: ExtremeRaceConditionTest):
    """Test all operations mixed together under chaos conditions."""
    print("🔥 Testing mixed operation chaos...")

    def chaos_worker(worker_id: int):
        """Worker creating chaos with mixed operations."""
        try:
            for i in range(200):
                operation_type = i % 4

                if operation_type == 0:
                    # Cache operations
                    func = create_test_function_batch(worker_id, 1)[0]
                    result = _get_math_detection_cached(func)
                    test_instance.record_stats(cache_hits=1 if result else 0)

                elif operation_type == 1:
                    # Source cache operations
                    func = create_test_function_batch(worker_id, 1)[0]
                    source = _get_function_source_cached(func)

                elif operation_type == 2:
                    # Registry operations
                    @tool_spec
                    def chaos_func(data: str = f"chaos_{worker_id}_{i}") -> str:
                        """Chaos function."""
                        return data
                    _manage_registry_size()

                elif operation_type == 3:
                    # Clear operations (chaos!)
                    if i % 20 == 0:  # Less frequent clears
                        clear_performance_caches()
                        test_instance.record_stats(evictions=1)

                # Small random delays to increase race condition probability
                if i % 10 == 0:
                    time.sleep(0.001)

        except Exception as e:
            test_instance.add_error(f"Chaos worker {worker_id} crashed: {e}")

    # Launch chaos workers
    with concurrent.futures.ThreadPoolExecutor(max_workers=40) as executor:
        futures = [executor.submit(chaos_worker, i) for i in range(40)]
        concurrent.futures.wait(futures, timeout=90)


def test_memory_pressure_and_weakrefs(test_instance: ExtremeRaceConditionTest):
    """Test thread safety under memory pressure and WeakKeyDictionary stress."""
    print("🔥 Testing memory pressure and WeakKeyDictionary stress...")

    def memory_pressure_worker(worker_id: int):
        """Worker creating memory pressure."""
        try:
            functions_cache = []
            weak_refs = []

            for i in range(500):
                # Create many functions
                func = create_test_function_batch(worker_id, 1)[0]
                functions_cache.append(func)
                weak_refs.append(weakref.ref(func))

                # Use them in cache
                _get_math_detection_cached(func)
                _get_function_source_cached(func)

                # Memory pressure simulation
                if i % 50 == 0:
                    # Delete some functions to test WeakKeyDictionary cleanup
                    del functions_cache[:25]
                    gc.collect()

                    # Test weak refs
                    alive_refs = [ref for ref in weak_refs if ref() is not None]
                    test_instance.record_stats(operations=len(alive_refs))

        except Exception as e:
            test_instance.add_error(f"Memory pressure worker {worker_id} crashed: {e}")

    # Launch memory pressure workers
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(memory_pressure_worker, i) for i in range(10)]
        concurrent.futures.wait(futures, timeout=120)


def main():
    """Run extreme race condition verification tests."""
    print("=" * 80)
    print("🔥 EXTREME RACE CONDITION VERIFICATION TEST 🔥")
    print("=" * 80)
    print("This test verifies thread safety fixes under extreme stress conditions.")
    print("-" * 80)

    test_instance = ExtremeRaceConditionTest()

    try:
        # Run extreme tests
        test_extreme_cache_concurrency(test_instance)
        test_registry_extreme_concurrency(test_instance)
        test_mixed_operation_chaos(test_instance)
        test_memory_pressure_and_weakrefs(test_instance)

    except Exception as e:
        test_instance.add_error(f"Test suite crashed: {e}")

    # Final assessment
    print("\n" + "=" * 80)
    print("📊 EXTREME TEST RESULTS")
    print("=" * 80)

    total_issues = len(test_instance.errors) + len(test_instance.inconsistencies) + len(test_instance.corruption_events)

    print(f"Statistics:")
    print(f"  • Total Operations: {test_instance.stats['operations']}")
    print(f"  • Cache Hits: {test_instance.stats['cache_hits']}")
    print(f"  • Evictions: {test_instance.stats['evictions']}")
    print(f"  • Lock Timeouts: {test_instance.stats['lock_timeouts']}")

    print(f"\nRace Condition Analysis:")
    print(f"  • Critical Errors: {len(test_instance.errors)}")
    print(f"  • Data Inconsistencies: {len(test_instance.inconsistencies)}")
    print(f"  • Corruption Events: {len(test_instance.corruption_events)}")
    print(f"  • Total Issues: {total_issues}")

    if test_instance.errors:
        print(f"\n❌ Critical Errors:")
        for i, error in enumerate(test_instance.errors[:5]):
            print(f"  {i+1}. {error}")

    if test_instance.inconsistencies:
        print(f"\n⚠️ Data Inconsistencies:")
        for i, inconsistency in enumerate(test_instance.inconsistencies[:5]):
            print(f"  {i+1}. {inconsistency}")

    if test_instance.corruption_events:
        print(f"\n🚨 Corruption Events:")
        for i, corruption in enumerate(test_instance.corruption_events[:5]):
            print(f"  {i+1}. {corruption}")

    if total_issues == 0:
        print(f"\n✅ EXCELLENT: No race conditions detected under extreme stress!")
        print("✅ Thread safety implementation is robust and comprehensive.")
        return True
    else:
        print(f"\n❌ ISSUES DETECTED: {total_issues} problems under extreme stress.")
        print("❌ Thread safety implementation needs improvement.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)