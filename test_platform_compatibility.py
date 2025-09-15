#!/usr/bin/env python3
"""
Test platform compatibility for AWS Bedrock and OpenAI tool specifications.

This test verifies that the enhanced tool registry correctly generates platform-specific
tool specifications while maintaining backward compatibility.
"""

import json
import sys
import os

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reasoning_library import (
    get_tool_specs, get_openai_tools, get_bedrock_tools,
    get_enhanced_tool_registry, TOOL_SPECS, OPENAI_TOOLS, BEDROCK_TOOLS
)


def test_backward_compatibility():
    """Test that legacy get_tool_specs() still works."""
    print("🔄 Testing backward compatibility...")

    legacy_specs = get_tool_specs()
    assert len(legacy_specs) > 0, "Legacy tool specs should not be empty"

    # Verify expected reasoning functions are present
    function_names = [spec['function']['name'] for spec in legacy_specs]
    expected_functions = ['apply_modus_ponens', 'predict_next_in_sequence', 'chain_of_thought_step']

    for func_name in expected_functions:
        assert func_name in function_names, f"Expected function {func_name} not found in legacy specs"

    print(f"✅ Legacy compatibility verified: {len(legacy_specs)} tools registered")


def test_openai_format():
    """Test OpenAI ChatCompletions API format."""
    print("🔄 Testing OpenAI format generation...")

    openai_tools = get_openai_tools()
    assert len(openai_tools) > 0, "OpenAI tools should not be empty"

    for tool in openai_tools:
        # Verify OpenAI format structure
        assert 'type' in tool, "OpenAI tool missing 'type' field"
        assert tool['type'] == 'function', "OpenAI tool type should be 'function'"
        assert 'function' in tool, "OpenAI tool missing 'function' field"

        function_spec = tool['function']
        assert 'name' in function_spec, "Function spec missing 'name'"
        assert 'description' in function_spec, "Function spec missing 'description'"
        assert 'parameters' in function_spec, "Function spec missing 'parameters'"

        # Verify parameters structure
        params = function_spec['parameters']
        assert 'type' in params, "Parameters missing 'type'"
        assert params['type'] == 'object', "Parameters type should be 'object'"
        assert 'properties' in params, "Parameters missing 'properties'"
        assert 'required' in params, "Parameters missing 'required'"

    print(f"✅ OpenAI format verified: {len(openai_tools)} tools")


def test_bedrock_format():
    """Test AWS Bedrock Converse API format."""
    print("🔄 Testing Bedrock format generation...")

    bedrock_tools = get_bedrock_tools()
    assert len(bedrock_tools) > 0, "Bedrock tools should not be empty"

    for tool in bedrock_tools:
        # Verify Bedrock format structure
        assert 'toolSpec' in tool, "Bedrock tool missing 'toolSpec' field"

        tool_spec = tool['toolSpec']
        assert 'name' in tool_spec, "ToolSpec missing 'name'"
        assert 'description' in tool_spec, "ToolSpec missing 'description'"
        assert 'inputSchema' in tool_spec, "ToolSpec missing 'inputSchema'"

        # Verify inputSchema structure
        input_schema = tool_spec['inputSchema']
        assert 'json' in input_schema, "InputSchema missing 'json'"

        json_schema = input_schema['json']
        assert 'type' in json_schema, "JSON schema missing 'type'"
        assert json_schema['type'] == 'object', "JSON schema type should be 'object'"
        assert 'properties' in json_schema, "JSON schema missing 'properties'"
        assert 'required' in json_schema, "JSON schema missing 'required'"

    print(f"✅ Bedrock format verified: {len(bedrock_tools)} tools")


def test_confidence_documentation():
    """Test that mathematical reasoning functions have enhanced confidence documentation."""
    print("🔄 Testing confidence documentation...")

    enhanced_registry = get_enhanced_tool_registry()
    mathematical_functions = [
        entry for entry in enhanced_registry
        if entry['metadata'].is_mathematical_reasoning
    ]

    assert len(mathematical_functions) > 0, "Should have mathematical reasoning functions"

    # Test that mathematical functions have enhanced descriptions
    openai_tools = get_openai_tools()
    for tool in openai_tools:
        func_name = tool['function']['name']
        description = tool['function']['description']

        # Check if this is a mathematical function
        math_entry = next((entry for entry in mathematical_functions
                          if entry['function'].__name__ == func_name), None)

        if math_entry:
            # Mathematical functions should have enhanced descriptions
            assert 'Mathematical Basis:' in description or 'Confidence Scoring:' in description, \
                f"Mathematical function {func_name} should have enhanced documentation"
            print(f"  📊 Enhanced documentation found for {func_name}")

    print(f"✅ Confidence documentation verified: {len(mathematical_functions)} mathematical functions")


def test_format_consistency():
    """Test that all formats have the same number of tools and consistent data."""
    print("🔄 Testing format consistency...")

    legacy_specs = get_tool_specs()
    openai_tools = get_openai_tools()
    bedrock_tools = get_bedrock_tools()

    # All formats should have the same number of tools
    assert len(legacy_specs) == len(openai_tools) == len(bedrock_tools), \
        f"Tool counts don't match: legacy={len(legacy_specs)}, openai={len(openai_tools)}, bedrock={len(bedrock_tools)}"

    # Function names should be consistent across formats
    legacy_names = {spec['function']['name'] for spec in legacy_specs}
    openai_names = {tool['function']['name'] for tool in openai_tools}
    bedrock_names = {tool['toolSpec']['name'] for tool in bedrock_tools}

    assert legacy_names == openai_names == bedrock_names, \
        "Function names should be consistent across all formats"

    print(f"✅ Format consistency verified: {len(legacy_specs)} tools across all formats")


def test_json_serialization():
    """Test that all generated formats are JSON serializable."""
    print("🔄 Testing JSON serialization...")

    try:
        # Test serialization of all formats
        legacy_json = json.dumps(get_tool_specs(), indent=2)
        openai_json = json.dumps(get_openai_tools(), indent=2)
        bedrock_json = json.dumps(get_bedrock_tools(), indent=2)

        # Verify we can parse them back
        json.loads(legacy_json)
        json.loads(openai_json)
        json.loads(bedrock_json)

        print("✅ JSON serialization verified for all formats")

    except (TypeError, ValueError) as e:
        raise AssertionError(f"JSON serialization failed: {e}")


def demonstrate_usage():
    """Demonstrate usage of the enhanced tool specification system."""
    print("\n🎯 Demonstrating Usage Examples")
    print("=" * 50)

    # Show a mathematical reasoning function with enhanced documentation
    openai_tools = get_openai_tools()
    math_tool = next((tool for tool in openai_tools
                     if 'predict_next_in_sequence' in tool['function']['name']), None)

    if math_tool:
        print("\n📊 Mathematical Reasoning Function (OpenAI Format):")
        print(json.dumps(math_tool, indent=2))

    # Show the same function in Bedrock format
    bedrock_tools = get_bedrock_tools()
    bedrock_math_tool = next((tool for tool in bedrock_tools
                             if 'predict_next_in_sequence' in tool['toolSpec']['name']), None)

    if bedrock_math_tool:
        print("\n🔗 Same Function (Bedrock Format):")
        print(json.dumps(bedrock_math_tool, indent=2))


def main():
    """Run all compatibility tests."""
    print("🚀 Starting Platform Compatibility Tests")
    print("=" * 50)

    try:
        test_backward_compatibility()
        test_openai_format()
        test_bedrock_format()
        test_confidence_documentation()
        test_format_consistency()
        test_json_serialization()

        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print(f"📈 Tool Specifications Generated:")
        print(f"   • Legacy format: {len(TOOL_SPECS)} tools")
        print(f"   • OpenAI format: {len(OPENAI_TOOLS)} tools")
        print(f"   • Bedrock format: {len(BEDROCK_TOOLS)} tools")

        demonstrate_usage()

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)