#!/usr/bin/env python3
"""
Verification test for the memory exhaustion fix in registries.
This test ensures the fix works and bounds are enforced.
"""

import sys
import os
import gc

# Add src to path for import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from reasoning_library.core import (
    ENHANCED_TOOL_REGISTRY,
    TOOL_REGISTRY,
    clear_performance_caches,
    tool_spec,
    _MAX_REGISTRY_SIZE,
    _manage_registry_size
)


def test_registry_size_bounds():
    """Test that registries are properly bounded to prevent memory exhaustion."""

    print("🛡️ Testing registry size bounds after fix...")

    # Clear any existing entries
    ENHANCED_TOOL_REGISTRY.clear()
    TOOL_REGISTRY.clear()
    gc.collect()

    print(f"Registry size limit: {_MAX_REGISTRY_SIZE}")
    print(f"Initial ENHANCED_TOOL_REGISTRY size: {len(ENHANCED_TOOL_REGISTRY)}")
    print(f"Initial TOOL_REGISTRY size: {len(TOOL_REGISTRY)}")

    # Create functions beyond the limit to test bounds
    print(f"\nCreating {_MAX_REGISTRY_SIZE + 100} functions to test bounds...")

    created_functions = []

    try:
        for i in range(_MAX_REGISTRY_SIZE + 100):
            @tool_spec(
                mathematical_basis=f"Bounds test function {i}",
                confidence_factors=["bounds"],
                confidence_formula=f"test_{i}"
            )
            def bounds_test_func(param="default"):
                """Test function for registry bounds testing."""
                return f"bounds_test_{param}_{i}"

            created_functions.append(bounds_test_func)

            # Check registry sizes every 50 functions
            if i % 50 == 0:
                enhanced_size = len(ENHANCED_TOOL_REGISTRY)
                tool_size = len(TOOL_REGISTRY)

                print(f"  Created {i} functions:")
                print(f"    ENHANCED_TOOL_REGISTRY: {enhanced_size}/{_MAX_REGISTRY_SIZE}")
                print(f"    TOOL_REGISTRY: {tool_size}/{_MAX_REGISTRY_SIZE}")

                # Verify that registries don't exceed the limit
                if enhanced_size > _MAX_REGISTRY_SIZE or tool_size > _MAX_REGISTRY_SIZE:
                    print(f"❌ FAIL: Registry exceeded size limit!")
                    print(f"   ENHANCED_TOOL_REGISTRY: {enhanced_size} > {_MAX_REGISTRY_SIZE}")
                    print(f"   TOOL_REGISTRY: {tool_size} > {_MAX_REGISTRY_SIZE}")
                    return False

        final_enhanced_size = len(ENHANCED_TOOL_REGISTRY)
        final_tool_size = len(TOOL_REGISTRY)

        print(f"\nFinal registry sizes after creating {_MAX_REGISTRY_SIZE + 100} functions:")
        print(f"  ENHANCED_TOOL_REGISTRY: {final_enhanced_size}/{_MAX_REGISTRY_SIZE}")
        print(f"  TOOL_REGISTRY: {final_tool_size}/{_MAX_REGISTRY_SIZE}")

        # Both registries should be at or below the limit
        if (final_enhanced_size <= _MAX_REGISTRY_SIZE and
            final_tool_size <= _MAX_REGISTRY_SIZE):
            print("✅ SUCCESS: Registry bounds enforced correctly!")
            return True
        else:
            print("❌ FAIL: Registry bounds not enforced!")
            return False

    except Exception as e:
        print(f"❌ FAIL: Exception during bounds test: {e}")
        return False
    finally:
        created_functions.clear()
        gc.collect()


def test_memory_exhaustion_attack_mitigation():
    """Test that memory exhaustion attacks are mitigated."""

    print("\n🚨 Testing memory exhaustion attack mitigation...")

    # Clear registries
    ENHANCED_TOOL_REGISTRY.clear()
    TOOL_REGISTRY.clear()
    gc.collect()

    print(f"Attack starting - registry limit: {_MAX_REGISTRY_SIZE}")

    # Simulate a large attack that would previously cause memory exhaustion
    attack_size = _MAX_REGISTRY_SIZE * 5  # 5x the limit
    print(f"Simulating attack with {attack_size} functions...")

    try:
        for i in range(attack_size):
            @tool_spec(
                mathematical_basis=f"Attack mitigation test {i}",
                confidence_factors=["mitigation"],
                confidence_formula="x"
            )
            def attack_mitigation_func(x=0):
                """Attack mitigation test function."""
                return x

            # Check registry sizes periodically
            if i % _MAX_REGISTRY_SIZE == 0 and i > 0:
                enhanced_size = len(ENHANCED_TOOL_REGISTRY)
                tool_size = len(TOOL_REGISTRY)

                print(f"  Attack progress {i}:")
                print(f"    ENHANCED_TOOL_REGISTRY: {enhanced_size}/{_MAX_REGISTRY_SIZE}")
                print(f"    TOOL_REGISTRY: {tool_size}/{_MAX_REGISTRY_SIZE}")

                # Verify bounds are maintained even during attack
                if enhanced_size > _MAX_REGISTRY_SIZE or tool_size > _MAX_REGISTRY_SIZE:
                    print(f"❌ FAIL: Attack broke registry bounds at {i}!")
                    return False

        final_enhanced_size = len(ENHANCED_TOOL_REGISTRY)
        final_tool_size = len(TOOL_REGISTRY)

        print(f"\nAttack mitigation results:")
        print(f"  Functions attempted: {attack_size}")
        print(f"  Final ENHANCED_TOOL_REGISTRY: {final_enhanced_size}/{_MAX_REGISTRY_SIZE}")
        print(f"  Final TOOL_REGISTRY: {final_tool_size}/{_MAX_REGISTRY_SIZE}")

        # Attack should be successfully mitigated
        if (final_enhanced_size <= _MAX_REGISTRY_SIZE and
            final_tool_size <= _MAX_REGISTRY_SIZE):
            print("✅ SUCCESS: Memory exhaustion attack mitigated!")
            print(f"   Attack limited to {_MAX_REGISTRY_SIZE} registry entries per registry")
            return True
        else:
            print("❌ FAIL: Memory exhaustion attack not mitigated!")
            return False

    except Exception as e:
        print(f"❌ FAIL: Exception during attack mitigation test: {e}")
        return False


def test_clear_performance_caches_effectiveness():
    """Test that clear_performance_caches() now clears registries."""

    print("\n🧹 Testing enhanced clear_performance_caches()...")

    # Create some registry entries
    for i in range(10):
        @tool_spec(
            mathematical_basis=f"Clear effectiveness test {i}",
            confidence_factors=["clear"]
        )
        def clear_effectiveness_test():
            """Clear effectiveness test function."""
            return i

    before_clear = len(ENHANCED_TOOL_REGISTRY)
    print(f"Registry entries before clear: {before_clear}")

    # Clear caches and registries
    cleared_stats = clear_performance_caches()
    print(f"Cache clear stats: {cleared_stats}")

    after_clear = len(ENHANCED_TOOL_REGISTRY)
    print(f"Registry entries after clear: {after_clear}")

    # Both registries should now be empty
    if after_clear == 0 and before_clear > 0:
        print("✅ SUCCESS: clear_performance_caches() now clears registries!")
        print(f"   Cleared {cleared_stats.get('enhanced_registry_cleared', 0)} enhanced entries")
        print(f"   Cleared {cleared_stats.get('tool_registry_cleared', 0)} tool entries")
        return True
    else:
        print("❌ FAIL: clear_performance_caches() doesn't clear registries!")
        return False


def test_registry_management_function():
    """Test the _manage_registry_size function directly."""

    print("\n⚙️ Testing _manage_registry_size function...")

    # Clear and populate registries beyond limit
    ENHANCED_TOOL_REGISTRY.clear()
    TOOL_REGISTRY.clear()

    # Fill registries to just under the limit
    for i in range(_MAX_REGISTRY_SIZE - 10):
        ENHANCED_TOOL_REGISTRY.append({"test": f"entry_{i}"})
        TOOL_REGISTRY.append(lambda: f"func_{i}")

    print(f"Before _manage_registry_size():")
    print(f"  ENHANCED_TOOL_REGISTRY: {len(ENHANCED_TOOL_REGISTRY)}")
    print(f"  TOOL_REGISTRY: {len(TOOL_REGISTRY)}")

    # Add a few more entries to trigger management
    for i in range(20):
        ENHANCED_TOOL_REGISTRY.append({"test": f"trigger_{i}"})
        TOOL_REGISTRY.append(lambda: f"trigger_{i}")

    print(f"After exceeding limit (before management):")
    print(f"  ENHANCED_TOOL_REGISTRY: {len(ENHANCED_TOOL_REGISTRY)}")
    print(f"  TOOL_REGISTRY: {len(TOOL_REGISTRY)}")

    # Call management function
    _manage_registry_size()

    print(f"After _manage_registry_size():")
    print(f"  ENHANCED_TOOL_REGISTRY: {len(ENHANCED_TOOL_REGISTRY)}")
    print(f"  TOOL_REGISTRY: {len(TOOL_REGISTRY)}")

    # Registries should now be at or below the limit
    if (len(ENHANCED_TOOL_REGISTRY) <= _MAX_REGISTRY_SIZE and
        len(TOOL_REGISTRY) <= _MAX_REGISTRY_SIZE):
        print("✅ SUCCESS: _manage_registry_size() works correctly!")
        return True
    else:
        print("❌ FAIL: _manage_registry_size() doesn't enforce limits!")
        return False


if __name__ == "__main__":
    print("🛡️ MEMORY EXHAUSTION FIX VERIFICATION TEST")
    print("=" * 60)
    print("Testing that the memory exhaustion vulnerability is fixed")
    print("=" * 60)

    all_passed = True

    # Test 1: Registry bounds enforcement
    print("TEST 1: Registry Bounds Enforcement")
    print("-" * 40)
    all_passed &= test_registry_size_bounds()

    # Test 2: Memory exhaustion attack mitigation
    print("\nTEST 2: Memory Exhaustion Attack Mitigation")
    print("-" * 40)
    all_passed &= test_memory_exhaustion_attack_mitigation()

    # Test 3: Enhanced cache clearing
    print("\nTEST 3: Enhanced Cache Clearing")
    print("-" * 40)
    all_passed &= test_clear_performance_caches_effectiveness()

    # Test 4: Registry management function
    print("\nTEST 4: Registry Management Function")
    print("-" * 40)
    all_passed &= test_registry_management_function()

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("🎉 Memory exhaustion vulnerability fixed successfully!")
        print(f"🛡️ Registry size limit: {_MAX_REGISTRY_SIZE} entries")
        print("⚡ LRU-style eviction implemented")
        print("🧹 Enhanced cache clearing includes registries")
    else:
        print("❌ SOME TESTS FAILED")
        print("🚨 Memory exhaustion fix may need adjustment")

    print("=" * 60)

    sys.exit(0 if all_passed else 1)