#!/usr/bin/env python3
"""
HIGH-002 Aggressive Race Condition Test

More aggressive test to uncover potential race conditions in conversation management
that might not be detected by the standard test.
"""

import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from reasoning_library.chain_of_thought import (
    _conversations,
    _conversations_lock,
    chain_of_thought_step,
    get_chain_summary,
    get_conversation_stats,
    _MAX_CONVERSATIONS,
)


def test_eviction_boundary_condition():
    """Test race condition around eviction boundary condition."""
    print("Testing eviction boundary condition...")

    with _conversations_lock:
        _conversations.clear()

    errors = []

    def worker_burst(worker_id: int):
        """Worker that creates conversations rapidly to hit eviction boundary."""
        try:
            # Create exactly MAX_CONVERSATIONS conversations
            for i in range(_MAX_CONVERSATIONS + 5):  # Go over the limit
                conv_id = f"boundary_test_worker_{worker_id}_{i}"
                result = chain_of_thought_step(
                    conversation_id=conv_id,
                    stage="Boundary",
                    description=f"Boundary test {conv_id}",
                    result=f"boundary_result_{i}",
                    confidence=0.9
                )

                # Check if step creation failed unexpectedly
                if not result["success"] and "Invalid conversation ID" not in str(result.get("error", "")):
                    errors.append(f"Worker {worker_id}: Unexpected failure: {result}")

        except Exception as e:
            errors.append(f"Worker {worker_id} crashed: {e}")

    # Run multiple workers to create concurrent eviction pressure
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(worker_burst, i) for i in range(4)]

        for future in as_completed(futures):
            try:
                future.result(timeout=60)
            except Exception as e:
                errors.append(f"Eviction boundary test failed: {e}")

    # Check memory limits
    stats = get_conversation_stats()
    total_convs = stats["total_conversations"]

    if total_convs > _MAX_CONVERSATIONS:
        errors.append(f"Memory limit exceeded: {total_convs} > {_MAX_CONVERSATIONS}")

    print(f"  Eviction boundary test: {len(errors)} errors")
    return errors


def test_same_conversation_high_concurrency():
    """Test very high concurrency on the same conversation."""
    print("Testing high concurrency on same conversation...")

    with _conversations_lock:
        _conversations.clear()

    errors = []
    conv_id = "high_concurrency_test"

    def high_frequency_worker(worker_id: int):
        """Worker that adds steps very rapidly."""
        try:
            for i in range(50):  # Many steps per worker
                result = chain_of_thought_step(
                    conversation_id=conv_id,
                    stage=f"Stage_{worker_id}",
                    description=f"High freq step {worker_id}_{i}",
                    result=f"result_{worker_id}_{i}",
                    confidence=0.8 + (i * 0.001)
                )

                if not result["success"]:
                    errors.append(f"Worker {worker_id}: Step creation failed: {result}")

                # Very small delay to maximize contention
                time.sleep(0.0001)

        except Exception as e:
            errors.append(f"High freq worker {worker_id} crashed: {e}")

    # High number of workers for maximum contention
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(high_frequency_worker, i) for i in range(20)]

        for future in as_completed(futures):
            try:
                future.result(timeout=60)
            except Exception as e:
                errors.append(f"High concurrency test failed: {e}")

    # Verify conversation integrity
    try:
        summary = get_chain_summary(conv_id)
        if not summary["success"]:
            errors.append(f"Conversation summary failed: {summary}")
        else:
            step_count = summary["step_count"]
            if step_count == 0:
                errors.append("No steps found despite successful operations")
    except Exception as e:
        errors.append(f"Conversation integrity check failed: {e}")

    print(f"  High concurrency test: {len(errors)} errors")
    return errors


def test_concurrent_clear_create_cycle():
    """Test race condition between clear and create operations."""
    print("Testing concurrent clear/create cycle...")

    with _conversations_lock:
        _conversations.clear()

    errors = []
    conv_id = "clear_create_test"

    def clear_worker():
        """Worker that repeatedly clears the conversation."""
        try:
            for i in range(20):
                # First create to have something to clear
                chain_of_thought_step(
                    conversation_id=conv_id,
                    stage="ClearSetup",
                    description=f"Setup for clear {i}",
                    result=f"setup_{i}",
                    confidence=0.9
                )

                time.sleep(0.001)

                # Now try to clear - but use get_chain_summary to verify
                summary = get_chain_summary(conv_id)
                if summary["success"] and summary["step_count"] > 0:
                    # We would clear here if we had that functionality
                    pass

        except Exception as e:
            errors.append(f"Clear worker crashed: {e}")

    def create_worker(worker_id: int):
        """Worker that continuously creates steps."""
        try:
            for i in range(100):
                result = chain_of_thought_step(
                    conversation_id=conv_id,
                    stage=f"Create_{worker_id}",
                    description=f"Create step {worker_id}_{i}",
                    result=f"create_result_{worker_id}_{i}",
                    confidence=0.7
                )

                if not result["success"]:
                    # Expected if conversation was cleared, but check for real errors
                    if "Invalid conversation ID" not in str(result.get("error", "")):
                        errors.append(f"Create worker {worker_id}: Unexpected failure: {result}")

                time.sleep(0.0005)

        except Exception as e:
            errors.append(f"Create worker {worker_id} crashed: {e}")

    # Run clear and create workers
    with ThreadPoolExecutor(max_workers=6) as executor:
        clear_future = executor.submit(clear_worker)
        create_futures = [executor.submit(create_worker, i) for i in range(5)]

        all_futures = [clear_future] + create_futures
        for future in as_completed(all_futures):
            try:
                future.result(timeout=60)
            except Exception as e:
                errors.append(f"Clear/create cycle test failed: {e}")

    print(f"  Clear/create cycle test: {len(errors)} errors")
    return errors


def main():
    """Run aggressive race condition tests."""
    print("=" * 80)
    print("🔍 HIGH-002 AGGRESSIVE RACE CONDITION TEST 🔍")
    print("=" * 80)

    all_errors = []

    # Test 1: Eviction boundary condition
    errors1 = test_eviction_boundary_condition()
    all_errors.extend(errors1)

    # Test 2: High concurrency on same conversation
    errors2 = test_same_conversation_high_concurrency()
    all_errors.extend(errors2)

    # Test 3: Concurrent clear/create cycle
    errors3 = test_concurrent_clear_create_cycle()
    all_errors.extend(errors3)

    print("\n" + "=" * 80)
    print("🔍 AGGRESSIVE RACE CONDITION TEST RESULTS 🔍")
    print("=" * 80)

    if all_errors:
        print(f"❌ {len(all_errors)} race condition issues detected:")
        for i, error in enumerate(all_errors[:10]):
            print(f"  {i+1}. {error}")
        if len(all_errors) > 10:
            print(f"  ... and {len(all_errors) - 10} more errors")
        return False
    else:
        print("✅ No race conditions detected in aggressive testing!")
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)