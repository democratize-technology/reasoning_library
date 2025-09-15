#!/usr/bin/env python3
"""
Test the actual registered functions to ensure they work with the improved confidence extraction.
"""

from core import get_openai_tools, get_bedrock_tools, get_enhanced_tool_registry
import json

def test_real_registered_functions():
    """Test the actual registered functions with improved confidence extraction."""
    print("=" * 80)
    print("TESTING REAL REGISTERED FUNCTIONS")
    print("=" * 80)

    # Get the enhanced registry
    registry = get_enhanced_tool_registry()
    print(f"Found {len(registry)} registered functions")

    for i, entry in enumerate(registry, 1):
        print(f"\n{i}. Function: {entry['function'].__name__}")
        print(f"   Mathematical: {entry['metadata'].is_mathematical_reasoning}")

        if entry['metadata'].confidence_documentation:
            print(f"   Confidence doc: {entry['metadata'].confidence_documentation}")
        else:
            print("   Confidence doc: None")

        if entry['metadata'].mathematical_basis:
            print(f"   Mathematical basis: {entry['metadata'].mathematical_basis}")

def test_openai_format_output():
    """Test OpenAI format includes improved confidence documentation."""
    print("\n\n" + "=" * 80)
    print("TESTING OPENAI FORMAT WITH IMPROVED CONFIDENCE DOCS")
    print("=" * 80)

    openai_tools = get_openai_tools()

    for i, tool in enumerate(openai_tools, 1):
        print(f"\n{i}. {tool['function']['name']}")
        description = tool['function']['description']

        # Check if confidence documentation is included
        if "Confidence Scoring:" in description:
            print("   ✅ Has confidence scoring documentation")
            # Extract the confidence line
            lines = description.split('\n')
            for line in lines:
                if line.strip().startswith("Confidence Scoring:"):
                    print(f"   📊 {line.strip()}")
        else:
            print("   ⚠️  No confidence scoring documentation")

        # Check for mathematical basis
        if "Mathematical Basis:" in description:
            print("   ✅ Has mathematical basis")
            lines = description.split('\n')
            for line in lines:
                if line.strip().startswith("Mathematical Basis:"):
                    print(f"   🧮 {line.strip()}")

def test_avoid_malformed_output():
    """Verify that we no longer generate malformed confidence output."""
    print("\n\n" + "=" * 80)
    print("VERIFYING NO MALFORMED OUTPUT")
    print("=" * 80)

    openai_tools = get_openai_tools()
    malformed_patterns = ['0, )', ':, r', ', ,', '=,', '*,', ': :']

    found_malformed = False
    for tool in openai_tools:
        description = tool['function']['description']
        for pattern in malformed_patterns:
            if pattern in description:
                print(f"❌ Found malformed pattern '{pattern}' in {tool['function']['name']}")
                found_malformed = True

    if not found_malformed:
        print("✅ No malformed patterns found in any tool descriptions!")

if __name__ == "__main__":
    test_real_registered_functions()
    test_openai_format_output()
    test_avoid_malformed_output()