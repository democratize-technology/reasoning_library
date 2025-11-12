#!/usr/bin/env python3
"""
Test for memory exhaustion vulnerability through unbounded cache pollution.
This test demonstrates the vulnerability and verifies the fix.
"""

import gc
import os
import sys

import psutil

# Add src to path for import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from reasoning_library.core import (
    ENHANCED_TOOL_REGISTRY,
    TOOL_REGISTRY,
    clear_performance_caches,
    tool_spec,
)


def get_memory_usage():
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def test_unbounded_registry_growth():
    """Test that demonstrates the memory exhaustion vulnerability."""

    print("🔍 Testing memory exhaustion vulnerability in unbounded registries...")

    # Clear any existing entries
    TOOL_REGISTRY.clear()
    ENHANCED_TOOL_REGISTRY.clear()
    gc.collect()

    initial_memory = get_memory_usage()
    print(f"Initial memory usage: {initial_memory:.2f} MB")
    print(f"Initial ENHANCED_TOOL_REGISTRY size: {len(ENHANCED_TOOL_REGISTRY)}")
    print(f"Initial TOOL_REGISTRY size: {len(TOOL_REGISTRY)}")

    # Create many functions with @tool_spec decorator to trigger registry growth
    print("\nCreating 1000 functions to test registry growth...")

    created_functions = []

    try:
        for i in range(1000):
            @tool_spec(
                mathematical_basis=f"Test function {i}",
                confidence_factors=["test"],
                confidence_formula="simple"
            )
            def test_func(param="default"):
                """Test function for memory exhaustion testing."""
                return f"test_{param}"

            created_functions.append(test_func)

            # Check memory every 100 functions
            if i % 100 == 0:
                current_memory = get_memory_usage()
                memory_increase = current_memory - initial_memory

                print(f"  Created {i} functions:")
                print(f"    ENHANCED_TOOL_REGISTRY: {len(ENHANCED_TOOL_REGISTRY)} entries")
                print(f"    TOOL_REGISTRY: {len(TOOL_REGISTRY)} entries")
                print(f"    Memory increase: {memory_increase:.2f} MB")

                # Fail test if memory growth is excessive (>50MB for 1000 functions)
                if memory_increase > 50:
                    print("❌ FAIL: Excessive memory growth detected!")
                    print(f"   Memory increased by {memory_increase:.2f} MB for {i} functions")
                    return False

                # Check that registries are growing unbounded (this is the vulnerability)
                if len(ENHANCED_TOOL_REGISTRY) != len(TOOL_REGISTRY):
                    print("❌ FAIL: Registry sizes don't match!")
                    print(f"   ENHANCED_TOOL_REGISTRY: {len(ENHANCED_TOOL_REGISTRY)}")
                    print(f"   TOOL_REGISTRY: {len(TOOL_REGISTRY)}")
                    return False

        final_memory = get_memory_usage()
        memory_increase = final_memory - initial_memory

        print("\nFinal results after creating 1000 functions:")
        print(f"  ENHANCED_TOOL_REGISTRY: {len(ENHANCED_TOOL_REGISTRY)} entries")
        print(f"  TOOL_REGISTRY: {len(TOOL_REGISTRY)} entries")
        print(f"  Total memory increase: {memory_increase:.2f} MB")

        # The vulnerability: registries grow unbounded
        if len(ENHANCED_TOOL_REGISTRY) == 1000 and len(TOOL_REGISTRY) == 1000:
            print("✅ VULNERABILITY CONFIRMED: Registries grow unbounded!")
            print("🚨 Each function creates 2 registry entries with no cleanup mechanism")
            return True
        else:
            print("❌ FAIL: Unexpected registry sizes")
            return False

    except Exception as e:
        print(f"❌ FAIL: Exception during test: {e}")
        return False
    finally:
        # Clean up
        created_functions.clear()
        gc.collect()


def test_memory_exhaustion_attack():
    """Test a simulated memory exhaustion attack."""

    print("\n🚨 Testing simulated memory exhaustion attack...")

    # Clear registries
    TOOL_REGISTRY.clear()
    ENHANCED_TOOL_REGISTRY.clear()
    gc.collect()

    initial_memory = get_memory_usage()
    print(f"Attack starting memory: {initial_memory:.2f} MB")

    # Simulate an attacker creating many functions
    print("Creating 5000 functions to simulate attack...")

    try:
        for batch in range(5):  # 5 batches of 1000
            batch_functions = []

            for i in range(1000):
                @tool_spec(
                    mathematical_basis=f"Attack function {batch}-{i}",
                    confidence_factors=["attack"],
                    confidence_formula="x*2"
                )
                def attack_func(x=0):
                    """Attack function for memory exhaustion testing."""
                    return x * 2

                batch_functions.append(attack_func)

            batch_memory = get_memory_usage()
            batch_increase = batch_memory - initial_memory

            print(f"  Batch {batch + 1}: {len(ENHANCED_TOOL_REGISTRY)} registry entries")
            print(f"  Memory increase: {batch_increase:.2f} MB")

            # If memory increase is >200MB, we've demonstrated the vulnerability
            if batch_increase > 200:
                print("❌ VULNERABILITY: Memory exhaustion attack successful!")
                print(f"   Attack caused {batch_increase:.2f} MB memory increase")
                return True

            # Clean up batch to isolate memory impact
            batch_functions.clear()
            gc.collect()

        final_memory = get_memory_usage()
        final_increase = final_memory - initial_memory

        print("\nAttack results:")
        print(f"  Final registry size: {len(ENHANCED_TOOL_REGISTRY)} entries")
        print(f"  Total memory increase: {final_increase:.2f} MB")

        # The vulnerability: memory remains high even after function cleanup
        if final_increase > 50 and len(ENHANCED_TOOL_REGISTRY) > 4000:
            print("❌ VULNERABILITY CONFIRMED: Memory exhaustion possible!")
            print("   Registry entries persist even after function objects are GC'd")
            return True
        else:
            print("ℹ️  No severe memory exhaustion detected in this test")
            return False

    except Exception as e:
        print(f"❌ FAIL: Exception during attack simulation: {e}")
        return False


def test_clear_performance_caches_ineffective():
    """Test that clear_performance_caches() doesn't help with registry growth."""

    print("\n🧹 Testing clear_performance_caches() effectiveness...")

    # Create some registry entries
    for i in range(10):
        @tool_spec(
            mathematical_basis=f"Clear test {i}",
            confidence_factors=["clear"]
        )
        def clear_test():
            """Clear test function."""
            return i

    before_clear = len(ENHANCED_TOOL_REGISTRY)
    print(f"Registry entries before clear: {before_clear}")

    # Try to clear caches
    cleared_stats = clear_performance_caches()
    print(f"Cache clear stats: {cleared_stats}")

    after_clear = len(ENHANCED_TOOL_REGISTRY)
    print(f"Registry entries after clear: {after_clear}")

    if after_clear == before_clear:
        print("❌ VULNERABILITY CONFIRMED: clear_performance_caches() doesn't clear registries!")
        print("   Registry entries persist despite cache clearing")
        return True
    else:
        print("✅ Registry cleared by cache clearing")
        return False


if __name__ == "__main__":
    print("🔍 MEMORY EXHAUSTION VULNERABILITY TEST")
    print("=" * 60)
    print("Testing for unbounded registry growth vulnerability")
    print("=" * 60)

    vulnerability_detected = False

    # Test 1: Basic unbounded growth
    print("TEST 1: Unbounded Registry Growth")
    print("-" * 40)
    vulnerability_detected |= test_unbounded_registry_growth()

    # Test 2: Memory exhaustion attack
    print("\nTEST 2: Memory Exhaustion Attack Simulation")
    print("-" * 40)
    vulnerability_detected |= test_memory_exhaustion_attack()

    # Test 3: Cache clearing ineffectiveness
    print("\nTEST 3: Cache Clearing Ineffectiveness")
    print("-" * 40)
    vulnerability_detected |= test_clear_performance_caches_ineffective()

    print("\n" + "=" * 60)
    if vulnerability_detected:
        print("❌ VULNERABILITIES DETECTED")
        print("🚨 CRITICAL: Memory exhaustion through unbounded cache pollution")
        print("📋 Issues found:")
        print("   - ENHANCED_TOOL_REGISTRY grows unbounded")
        print("   - TOOL_REGISTRY grows unbounded")
        print("   - No cleanup mechanism for registry entries")
        print("   - Memory persists even after functions are garbage collected")
        print("   - clear_performance_caches() doesn't address registry growth")
        print("\n⚠️  IMMEDIATE FIX REQUIRED")
    else:
        print("✅ NO OBVIOUS VULNERABILITIES DETECTED")
        print("📊 Tests completed without detecting memory exhaustion issues")

    print("=" * 60)

    sys.exit(1 if vulnerability_detected else 0)
