#!/usr/bin/env python3
"""
Test for race conditions in keyword extraction.
"""

import sys
import os
import threading
import concurrent.futures
from time import perf_counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from reasoning_library.abductive import _extract_keywords

def test_race_condition():
    """Test if race conditions exist in keyword extraction."""
    test_text = "server deployment database cpu memory slow error performance network"

    num_threads = 50
    iterations_per_thread = 100

    results = []

    def worker():
        thread_results = []
        for i in range(iterations_per_thread):
            result = _extract_keywords(test_text)
            thread_results.append(result)
        return thread_results

    start_time = perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker) for _ in range(num_threads)]

        for future in concurrent.futures.as_completed(futures):
            try:
                thread_results = future.result(timeout=10)
                results.extend(thread_results)
            except Exception as e:
                print(f"Exception: {e}")
                return False

    end_time = perf_counter()

    print(f"Completed {len(results)} extractions in {end_time - start_time:.4f} seconds")
    print(f"Expected: {num_threads * iterations_per_thread} results")

    # Check if all results are identical
    if results:
        first_result = results[0]
        inconsistent = 0

        for i, result in enumerate(results):
            if result != first_result:
                inconsistent += 1
                if inconsistent <= 5:  # Only print first few
                    print(f"Inconsistent result {i}: {result} vs {first_result}")

        print(f"Total inconsistent results: {inconsistent}/{len(results)}")
        return inconsistent == 0

    return False

if __name__ == "__main__":
    print("Testing for race conditions in keyword extraction...")
    is_safe = test_race_condition()
    print(f"Thread safety test: {'PASSED' if is_safe else 'FAILED'}")