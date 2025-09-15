#!/usr/bin/env python3
"""
Final verification test to ensure the confidence extraction fix works end-to-end.
"""

# Import the modules to register the functions
import inductive
import deductive
from core import get_openai_tools, get_bedrock_tools, get_enhanced_tool_registry

def test_end_to_end_confidence_fix():
    """Test the complete end-to-end confidence extraction fix."""
    print("=" * 80)
    print("FINAL END-TO-END VERIFICATION")
    print("=" * 80)

    # Get the enhanced registry
    registry = get_enhanced_tool_registry()
    print(f"Found {len(registry)} registered functions")

    mathematical_count = 0
    confidence_doc_count = 0

    for i, entry in enumerate(registry, 1):
        func_name = entry['function'].__name__
        is_math = entry['metadata'].is_mathematical_reasoning
        confidence_doc = entry['metadata'].confidence_documentation

        print(f"\n{i}. {func_name}")
        print(f"   Mathematical: {is_math}")

        if is_math:
            mathematical_count += 1
            if confidence_doc:
                confidence_doc_count += 1
                print(f"   ✅ Confidence: {confidence_doc}")

                # Check for malformed output
                malformed_indicators = ['0, )', ':, r', ', ,', '=,', '*,']
                is_malformed = any(indicator in confidence_doc for indicator in malformed_indicators)
                if is_malformed:
                    print(f"   ❌ MALFORMED: Contains bad patterns")
                else:
                    print(f"   ✅ Clean confidence documentation")
            else:
                print(f"   ⚠️  No confidence doc")
        else:
            print(f"   📝 Non-mathematical function")

    print(f"\n📊 SUMMARY")
    print(f"   Total functions: {len(registry)}")
    print(f"   Mathematical functions: {mathematical_count}")
    print(f"   With confidence docs: {confidence_doc_count}")

def test_specific_function_outputs():
    """Test specific functions that should have good confidence documentation."""
    print("\n\n" + "=" * 80)
    print("TESTING SPECIFIC FUNCTION OUTPUTS")
    print("=" * 80)

    registry = get_enhanced_tool_registry()

    target_functions = ['predict_next_in_sequence', 'find_pattern_description']

    for target_func in target_functions:
        found = False
        for entry in registry:
            if entry['function'].__name__ == target_func:
                found = True
                confidence_doc = entry['metadata'].confidence_documentation
                print(f"\n🎯 {target_func}")
                print(f"   Confidence doc: {confidence_doc}")

                if confidence_doc:
                    # Check for expected patterns
                    expected_patterns = ['data sufficiency', 'pattern quality', 'complexity']
                    found_patterns = [p for p in expected_patterns if p in confidence_doc.lower()]
                    print(f"   Expected patterns found: {found_patterns}")
                    if found_patterns:
                        print(f"   ✅ Contains meaningful confidence factors")
                    else:
                        print(f"   ⚠️  Missing expected patterns")
                break

        if not found:
            print(f"\n❌ Function {target_func} not found in registry")

def test_openai_tool_descriptions():
    """Test OpenAI tool descriptions for clean confidence documentation."""
    print("\n\n" + "=" * 80)
    print("TESTING OPENAI TOOL DESCRIPTIONS")
    print("=" * 80)

    openai_tools = get_openai_tools()

    for tool in openai_tools:
        name = tool['function']['name']
        description = tool['function']['description']

        print(f"\n🔧 {name}")

        if "Confidence Scoring:" in description:
            lines = description.split('\n')
            for line in lines:
                if line.strip().startswith("Confidence Scoring:"):
                    conf_line = line.strip()
                    print(f"   📊 {conf_line}")

                    # Check for malformed patterns
                    malformed_indicators = ['0, )', ':, r', ', ,', '=,', '*,']
                    is_malformed = any(indicator in conf_line for indicator in malformed_indicators)
                    if is_malformed:
                        print(f"   ❌ MALFORMED OUTPUT DETECTED!")
                    else:
                        print(f"   ✅ Clean confidence scoring description")
                    break
        else:
            print(f"   📝 No confidence scoring (non-mathematical function)")

if __name__ == "__main__":
    test_end_to_end_confidence_fix()
    test_specific_function_outputs()
    test_openai_tool_descriptions()