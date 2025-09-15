#!/usr/bin/env python3
"""
Example usage of the Reasoning Library

This script demonstrates the key features and usage patterns
described in the README.md file.
"""

import json

from reasoning_library.core import ReasoningChain

# Import core functionality
from reasoning_library.deductive import apply_modus_ponens

# Try to import inductive features, but make them optional for now
try:
    from reasoning_library.inductive import (
        find_pattern_description,
        predict_next_in_sequence,
    )

    INDUCTIVE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Inductive reasoning not available: {e}")
    INDUCTIVE_AVAILABLE = False

# Try to import tool specs, but make them optional
try:
    from reasoning_library import TOOL_SPECS

    TOOL_SPECS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Tool specs not available: {e}")
    TOOL_SPECS_AVAILABLE = False


def print_separator(title: str) -> None:
    """Print a formatted section separator."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def demonstrate_deductive_reasoning() -> None:
    """Demonstrate deductive reasoning with Modus Ponens."""
    print_separator("DEDUCTIVE REASONING EXAMPLE")

    chain = ReasoningChain()

    print(
        "Testing Modus Ponens rule: If P is true, and (P -> Q) is true, then Q is true."
    )
    print()

    # Case 1: P=True, Q=True (valid inference)
    result1 = apply_modus_ponens(True, True, reasoning_chain=chain)
    print(f"Modus Ponens (P=True, Q=True): {result1}")

    # Case 2: P=True, Q=False (invalid - P->Q would be false)
    result2 = apply_modus_ponens(True, False, reasoning_chain=chain)
    print(f"Modus Ponens (P=True, Q=False): {result2}")

    print("\nReasoning Chain Summary:")
    print(chain.get_summary())


def demonstrate_inductive_reasoning() -> None:
    """Demonstrate inductive reasoning with pattern recognition."""
    print_separator("INDUCTIVE REASONING EXAMPLE")

    if not INDUCTIVE_AVAILABLE:
        print("❌ Inductive reasoning is not available due to import issues.")
        print("   This is likely due to missing numpy dependency.")
        print("   Please install numpy: pip install numpy==1.26.4")
        return

    chain = ReasoningChain()

    # Arithmetic sequence
    seq = [1.0, 2.0, 3.0, 4.0]
    chain.add_step(
        stage="Inductive Reasoning", description=f"Analyzing sequence {seq}", result=seq
    )

    pattern = find_pattern_description(seq, reasoning_chain=chain)
    predicted = predict_next_in_sequence(seq, reasoning_chain=chain)

    print(f"Sequence: {seq}")
    print(f"Pattern: {pattern}")
    print(f"Predicted next: {predicted}")

    print("\nReasoning Chain Summary:")
    print(chain.get_summary())

    # Additional example: Geometric sequence
    print("\n" + "-" * 40)
    print("Additional Example: Geometric Sequence")
    print("-" * 40)

    chain2 = ReasoningChain()
    geo_seq = [2.0, 4.0, 8.0, 16.0]
    chain2.add_step(
        stage="Inductive Reasoning",
        description=f"Analyzing sequence {geo_seq}",
        result=geo_seq,
    )

    geo_pattern = find_pattern_description(geo_seq, reasoning_chain=chain2)
    geo_predicted = predict_next_in_sequence(geo_seq, reasoning_chain=chain2)

    print(f"Sequence: {geo_seq}")
    print(f"Pattern: {geo_pattern}")
    print(f"Predicted next: {geo_predicted}")


def demonstrate_llm_tool_specs() -> None:
    """Demonstrate LLM tool specification generation."""
    print_separator("LLM TOOL SPECIFICATION EXAMPLE")

    if not TOOL_SPECS_AVAILABLE:
        print("❌ Tool specifications are not available due to import issues.")
        print("   This may be related to the numpy dependency problem.")
        return

    print("Generated JSON Schema tool specifications for LLM integration:")
    print("(These can be 'just dropped in' to your LLM's tool configuration)")
    print()

    # Pretty print the tool specifications
    print(json.dumps(TOOL_SPECS, indent=2))

    print(f"\nTotal tools available: {len(TOOL_SPECS)}")
    if TOOL_SPECS:
        print("Available tools:")
        for i, tool in enumerate(TOOL_SPECS, 1):
            function_name = tool.get("function", {}).get("name", "Unknown")
            description = tool.get("function", {}).get("description", "No description")
            print(f"  {i}. {function_name}: {description}")


def demonstrate_reasoning_chain_features() -> None:
    """Demonstrate additional ReasoningChain features."""
    print_separator("REASONING CHAIN FEATURES")

    chain = ReasoningChain()

    # Add some reasoning steps manually
    chain.add_step(
        stage="Problem Analysis",
        description="Identifying the core problem",
        result="Problem: Need to find pattern in sequence",
        confidence=0.9,
        evidence="User provided sequence [1, 4, 7, 10]",
        assumptions=["Sequence is arithmetic", "Pattern continues"],
    )

    chain.add_step(
        stage="Pattern Recognition",
        description="Analyzing differences between consecutive terms",
        result="Arithmetic progression with difference 3",
        confidence=0.95,
        evidence="Differences: 4-1=3, 7-4=3, 10-7=3",
        assumptions=["Pattern is linear"],
    )

    chain.add_step(
        stage="Prediction",
        description="Predicting next term in sequence",
        result=13,
        confidence=0.95,
        evidence="10 + 3 = 13",
        assumptions=["Pattern continues unchanged"],
    )

    print("Reasoning Chain with detailed metadata:")
    print(chain.get_summary())

    print(f"\nLast result: {chain.last_result}")
    print(f"Total steps: {len(chain.steps)}")

    # Demonstrate clearing
    print("\nClearing chain...")
    chain.clear()
    print(f"Steps after clearing: {len(chain.steps)}")


def main() -> None:
    """Main demonstration function."""
    print("🧠 Reasoning Library Demonstration")
    print("A showcase of functional reasoning capabilities")

    try:
        demonstrate_deductive_reasoning()
        demonstrate_inductive_reasoning()
        demonstrate_reasoning_chain_features()
        demonstrate_llm_tool_specs()

        print_separator("DEMONSTRATION COMPLETE")
        print("✅ All examples completed successfully!")
        print("📚 Check the README.md for more detailed explanations.")
        print("🔧 Extend the library by adding new reasoning modules.")

    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        print("Please check your installation and dependencies.")
        raise


if __name__ == "__main__":
    main()
