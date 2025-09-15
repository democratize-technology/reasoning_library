#!/usr/bin/env python3
"""
Test core platform compatibility for AWS Bedrock and OpenAI tool specifications.

This test verifies the core functionality without requiring full module dependencies.
"""

import json
import sys
import os

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test the core functionality directly
from core import (
    tool_spec, get_tool_specs, get_openai_tools, get_bedrock_tools,
    get_enhanced_tool_registry, ToolMetadata, _openai_format, _bedrock_format
)


@tool_spec
def test_mathematical_function(sequence: list, confidence: float = 0.8) -> float:
    """
    Test mathematical reasoning function for pattern prediction.

    This function uses geometric progression analysis with coefficient_of_variation
    calculations and confidence scoring based on data sufficiency factors.

    Args:
        sequence: List of numbers to analyze
        confidence: Base confidence level

    Returns:
        Predicted next value with statistical confidence
    """
    # Simple arithmetic progression for testing
    if len(sequence) >= 2:
        diff = sequence[-1] - sequence[-2]
        result = sequence[-1] + diff
        return result
    return 0.0


@tool_spec
def test_simple_function(text: str, count: int = 1) -> str:
    """
    Simple function for testing basic tool specification generation.

    Args:
        text: Input text to process
        count: Number of repetitions

    Returns:
        Processed text result
    """
    return text * count


def test_enhanced_registry():
    """Test that enhanced registry captures metadata correctly."""
    print("🔄 Testing enhanced registry...")

    registry = get_enhanced_tool_registry()
    assert len(registry) >= 2, f"Expected at least 2 tools, got {len(registry)}"

    # Find the mathematical function
    math_entry = next((entry for entry in registry
                      if entry['function'].__name__ == 'test_mathematical_function'), None)

    assert math_entry is not None, "Mathematical function not found in registry"
    assert math_entry['metadata'].is_mathematical_reasoning, "Should detect mathematical reasoning"
    assert math_entry['metadata'].mathematical_basis is not None, "Should have mathematical basis"

    print(f"✅ Enhanced registry verified: {len(registry)} entries")
    return True


def test_openai_format():
    """Test OpenAI format generation."""
    print("🔄 Testing OpenAI format...")

    openai_tools = get_openai_tools()
    assert len(openai_tools) >= 2, "Should have at least 2 OpenAI tools"

    for tool in openai_tools:
        assert tool['type'] == 'function', "Type should be 'function'"
        assert 'function' in tool, "Should have 'function' field"

        func = tool['function']
        assert 'name' in func, "Should have 'name'"
        assert 'description' in func, "Should have 'description'"
        assert 'parameters' in func, "Should have 'parameters'"

        params = func['parameters']
        assert params['type'] == 'object', "Parameters type should be 'object'"
        assert 'properties' in params, "Should have 'properties'"
        assert 'required' in params, "Should have 'required'"

    print(f"✅ OpenAI format verified: {len(openai_tools)} tools")
    return True


def test_bedrock_format():
    """Test Bedrock format generation."""
    print("🔄 Testing Bedrock format...")

    bedrock_tools = get_bedrock_tools()
    assert len(bedrock_tools) >= 2, "Should have at least 2 Bedrock tools"

    for tool in bedrock_tools:
        assert 'toolSpec' in tool, "Should have 'toolSpec' field"

        spec = tool['toolSpec']
        assert 'name' in spec, "Should have 'name'"
        assert 'description' in spec, "Should have 'description'"
        assert 'inputSchema' in spec, "Should have 'inputSchema'"

        schema = spec['inputSchema']
        assert 'json' in schema, "Should have 'json' field"

        json_schema = schema['json']
        assert json_schema['type'] == 'object', "JSON schema type should be 'object'"
        assert 'properties' in json_schema, "Should have 'properties'"
        assert 'required' in json_schema, "Should have 'required'"

    print(f"✅ Bedrock format verified: {len(bedrock_tools)} tools")
    return True


def test_confidence_enhancement():
    """Test confidence documentation enhancement."""
    print("🔄 Testing confidence documentation...")

    openai_tools = get_openai_tools()
    math_tool = next((tool for tool in openai_tools
                     if tool['function']['name'] == 'test_mathematical_function'), None)

    assert math_tool is not None, "Mathematical test function not found"

    description = math_tool['function']['description']
    assert 'Mathematical Basis:' in description, "Should have mathematical basis documentation"

    print("✅ Confidence documentation verified")
    return True


def test_backward_compatibility():
    """Test backward compatibility with legacy format."""
    print("🔄 Testing backward compatibility...")

    legacy_specs = get_tool_specs()
    assert len(legacy_specs) >= 2, "Should have legacy specs"

    # Verify structure matches original format
    for spec in legacy_specs:
        assert spec['type'] == 'function', "Type should be 'function'"
        assert 'function' in spec, "Should have 'function' field"

        func = spec['function']
        assert 'name' in func, "Should have 'name'"
        assert 'description' in func, "Should have 'description'"
        assert 'parameters' in func, "Should have 'parameters'"

    print(f"✅ Backward compatibility verified: {len(legacy_specs)} tools")
    return True


def test_json_serialization():
    """Test JSON serialization of all formats."""
    print("🔄 Testing JSON serialization...")

    try:
        legacy_json = json.dumps(get_tool_specs(), indent=2)
        openai_json = json.dumps(get_openai_tools(), indent=2)
        bedrock_json = json.dumps(get_bedrock_tools(), indent=2)

        # Verify parsing
        json.loads(legacy_json)
        json.loads(openai_json)
        json.loads(bedrock_json)

        print("✅ JSON serialization verified")
        return True

    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        return False


def demonstrate_formats():
    """Demonstrate the different formats."""
    print("\n🎯 Format Examples")
    print("=" * 50)

    # Get the mathematical function from each format
    legacy_specs = get_tool_specs()
    openai_tools = get_openai_tools()
    bedrock_tools = get_bedrock_tools()

    math_legacy = next((s for s in legacy_specs if s['function']['name'] == 'test_mathematical_function'), None)
    math_openai = next((t for t in openai_tools if t['function']['name'] == 'test_mathematical_function'), None)
    math_bedrock = next((t for t in bedrock_tools if t['toolSpec']['name'] == 'test_mathematical_function'), None)

    if math_legacy:
        print("\n📋 Legacy Format:")
        print(json.dumps(math_legacy, indent=2))

    if math_openai:
        print("\n🤖 OpenAI Format:")
        print(json.dumps(math_openai, indent=2))

    if math_bedrock:
        print("\n☁️ Bedrock Format:")
        print(json.dumps(math_bedrock, indent=2))


def main():
    """Run all tests."""
    print("🚀 Core Platform Compatibility Tests")
    print("=" * 50)

    tests = [
        test_enhanced_registry,
        test_openai_format,
        test_bedrock_format,
        test_confidence_enhancement,
        test_backward_compatibility,
        test_json_serialization
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1

    print("\n" + "=" * 50)
    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
        print(f"✅ {passed} tests completed successfully")

        demonstrate_formats()
        return True
    else:
        print(f"❌ {failed} tests failed, {passed} tests passed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)