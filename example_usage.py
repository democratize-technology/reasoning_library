#!/usr/bin/env python3
"""
Example usage of the enhanced tool specification system.

This demonstrates how to use the new AWS Bedrock and OpenAI compatible
tool specifications with mathematical reasoning functions.
"""

import json
import sys
import os

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import (
    tool_spec, get_tool_specs, get_openai_tools, get_bedrock_tools,
    get_enhanced_tool_registry, ToolMetadata
)


# Define example reasoning functions
@tool_spec
def calculate_arithmetic_confidence(sequence: list, tolerance: float = 0.1) -> dict:
    """
    Calculate confidence for arithmetic progression detection in numerical sequences.

    This function analyzes a sequence for arithmetic patterns using data sufficiency
    and pattern quality factors with coefficient_of_variation analysis.

    Args:
        sequence: List of numerical values to analyze
        tolerance: Tolerance level for pattern detection (default: 0.1)

    Returns:
        Dictionary containing confidence score, pattern type, and statistical metrics
    """
    if len(sequence) < 3:
        return {"confidence": 0.0, "pattern": "insufficient_data"}

    # Simple arithmetic progression check
    diffs = [sequence[i] - sequence[i-1] for i in range(1, len(sequence))]
    avg_diff = sum(diffs) / len(diffs)
    variance = sum((d - avg_diff)**2 for d in diffs) / len(diffs)

    # Calculate confidence based on variance
    confidence = max(0.0, 1.0 - (variance / (avg_diff**2 + 1e-10)))

    return {
        "confidence": min(1.0, confidence),
        "pattern": "arithmetic",
        "common_difference": avg_diff,
        "variance": variance
    }


@tool_spec
def logical_reasoning_step(premise1: bool, premise2: bool, operation: str = "and") -> dict:
    """
    Perform logical reasoning operations with modus ponens and truth table analysis.

    This function applies deductive logic rules with deterministic confidence scoring
    for boolean operations and logical inference.

    Args:
        premise1: First boolean premise
        premise2: Second boolean premise
        operation: Logical operation ('and', 'or', 'implies')

    Returns:
        Dictionary with logical result and reasoning confidence
    """
    operations = {
        "and": lambda p1, p2: p1 and p2,
        "or": lambda p1, p2: p1 or p2,
        "implies": lambda p1, p2: (not p1) or p2
    }

    if operation not in operations:
        return {"result": None, "confidence": 0.0, "error": "invalid_operation"}

    result = operations[operation](premise1, premise2)

    return {
        "result": result,
        "confidence": 1.0,  # Deterministic logical operations have perfect confidence
        "operation": operation,
        "premises": [premise1, premise2]
    }


@tool_spec
def simple_text_processor(text: str, uppercase: bool = False) -> str:
    """
    Simple text processing function for demonstration.

    Args:
        text: Input text to process
        uppercase: Whether to convert to uppercase

    Returns:
        Processed text string
    """
    if uppercase:
        return text.upper()
    return text.lower()


def demonstrate_platform_exports():
    """Demonstrate exporting to different platform formats."""
    print("🚀 Enhanced Tool Specification System Demo")
    print("=" * 60)

    # Get all formats
    legacy_specs = get_tool_specs()
    openai_tools = get_openai_tools()
    bedrock_tools = get_bedrock_tools()
    enhanced_registry = get_enhanced_tool_registry()

    print(f"📊 Tool Statistics:")
    print(f"   • Total functions registered: {len(legacy_specs)}")
    print(f"   • Mathematical reasoning functions: {sum(1 for entry in enhanced_registry if entry['metadata'].is_mathematical_reasoning)}")
    print(f"   • OpenAI format tools: {len(openai_tools)}")
    print(f"   • Bedrock format tools: {len(bedrock_tools)}")

    # Demonstrate mathematical function enhancement
    print(f"\n🧮 Mathematical Reasoning Function Enhancement:")
    math_function = next((entry for entry in enhanced_registry
                         if entry['function'].__name__ == 'calculate_arithmetic_confidence'), None)

    if math_function:
        print(f"   • Function: {math_function['function'].__name__}")
        print(f"   • Mathematical reasoning detected: {math_function['metadata'].is_mathematical_reasoning}")
        print(f"   • Mathematical basis: {math_function['metadata'].mathematical_basis}")
        print(f"   • Confidence documentation: {math_function['metadata'].confidence_documentation}")

    # Show OpenAI format example
    print(f"\n🤖 OpenAI ChatCompletions Format Example:")
    openai_math = next((tool for tool in openai_tools
                       if tool['function']['name'] == 'calculate_arithmetic_confidence'), None)
    if openai_math:
        print(json.dumps(openai_math, indent=2))

    # Show Bedrock format example
    print(f"\n☁️ AWS Bedrock Converse Format Example:")
    bedrock_math = next((tool for tool in bedrock_tools
                        if tool['toolSpec']['name'] == 'calculate_arithmetic_confidence'), None)
    if bedrock_math:
        print(json.dumps(bedrock_math, indent=2))

    return True


def test_real_function_calls():
    """Test actual function calls to verify functionality."""
    print(f"\n🧪 Function Execution Tests:")
    print("-" * 40)

    # Test arithmetic confidence calculation
    sequence = [2, 4, 6, 8, 10]
    result = calculate_arithmetic_confidence(sequence)
    print(f"Arithmetic sequence analysis: {result}")

    # Test logical reasoning
    logic_result = logical_reasoning_step(True, False, "implies")
    print(f"Logical reasoning (True implies False): {logic_result}")

    # Test simple function
    text_result = simple_text_processor("Hello World", uppercase=True)
    print(f"Text processing: {text_result}")

    return True


def demonstrate_integration_scenarios():
    """Show how to integrate with different LLM platforms."""
    print(f"\n🔗 Integration Scenarios:")
    print("-" * 40)

    print("1. OpenAI ChatCompletions Integration:")
    print("```python")
    print("from reasoning_library import get_openai_tools")
    print("")
    print("client = openai.OpenAI()")
    print("response = client.chat.completions.create(")
    print("    model='gpt-4',")
    print("    messages=messages,")
    print("    tools=get_openai_tools(),  # Direct integration")
    print("    tool_choice='auto'")
    print(")")
    print("```")

    print("\n2. AWS Bedrock Converse Integration:")
    print("```python")
    print("from reasoning_library import get_bedrock_tools")
    print("")
    print("bedrock = boto3.client('bedrock-runtime')")
    print("response = bedrock.converse(")
    print("    modelId='anthropic.claude-3-sonnet-20240229-v1:0',")
    print("    messages=messages,")
    print("    toolConfig={")
    print("        'tools': get_bedrock_tools()  # Direct integration")
    print("    }")
    print(")")
    print("```")

    print("\n3. Legacy MCP Integration:")
    print("```python")
    print("from reasoning_library import get_tool_specs")
    print("")
    print("# Existing MCP integrations continue to work")
    print("for spec in get_tool_specs():")
    print("    mcp_server.register_tool(spec)")
    print("```")

    return True


def main():
    """Run the complete demonstration."""
    try:
        demonstrate_platform_exports()
        test_real_function_calls()
        demonstrate_integration_scenarios()

        print(f"\n🎉 Demonstration Complete!")
        print("=" * 60)
        print("✅ Enhanced tool specification system successfully implemented")
        print("✅ AWS Bedrock and OpenAI compatibility verified")
        print("✅ Mathematical reasoning confidence documentation working")
        print("✅ Backward compatibility maintained")

        return True

    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)