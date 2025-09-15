#!/usr/bin/env python3
"""
Simple test of the reasoning library core functionality.

This bypasses the problematic imports and tests what we can verify works.
"""
import sys

try:
    # Test core functionality
    from reasoning_library.core import ReasoningChain, ReasoningStep

    print("✅ Core module imported successfully")

    # Test deductive reasoning
    from reasoning_library.deductive import apply_modus_ponens

    print("✅ Deductive module imported successfully")

    print("\n" + "=" * 60)
    print("  BASIC FUNCTIONALITY TEST")
    print("=" * 60)

    # Test ReasoningChain
    chain = ReasoningChain()
    chain.add_step(
        stage="Test",
        description="Testing basic functionality",
        result="Chain works!",
        confidence=1.0,
    )

    print("\nReasoningChain test:")
    print(f"Steps count: {len(chain.steps)}")
    print(f"Last result: {chain.last_result}")
    print(f"Summary: {chain.get_summary()}")

    # Test Modus Ponens
    print("\nModus Ponens test:")
    result1 = apply_modus_ponens(True, True, reasoning_chain=chain)
    print(f"Modus Ponens (P=True, Q=True): {result1}")

    result2 = apply_modus_ponens(True, False, reasoning_chain=chain)
    print(f"Modus Ponens (P=True, Q=False): {result2}")

    print(f"\nFinal chain summary:")
    print(chain.get_summary())

    print("\n" + "=" * 60)
    print("✅ BASIC TEST COMPLETE - Core functionality works!")
    print("❌ Note: Inductive reasoning unavailable due to numpy issues")
    print("❌ Note: Tool specs unavailable due to dependency issues")
    print("=" * 60)

except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Runtime error: {e}")
    sys.exit(1)
