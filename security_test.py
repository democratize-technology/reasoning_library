#!/usr/bin/env python3
"""
Security test script to validate the critical vulnerability fixes.
Tests for ReDoS, prototype pollution, and code exposure vulnerabilities.
"""

import sys
import time
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import (
    _detect_mathematical_reasoning,
    _safe_copy_spec,
    _openai_format,
    _bedrock_format,
    MAX_SOURCE_CODE_SIZE
)

def test_redos_protection():
    """Test ReDoS vulnerability protection."""
    print("🔍 Testing ReDoS protection...")

    # Create a function with large source code to test size limit
    large_source = "# " + "A" * (MAX_SOURCE_CODE_SIZE + 1000)  # Exceeds limit

    def dummy_func():
        """A dummy function for testing."""
        pass

    # Monkey patch to simulate large source
    import inspect
    original_getsource = inspect.getsource

    def mock_getsource(func):
        if func == dummy_func:
            return large_source
        return original_getsource(func)

    inspect.getsource = mock_getsource

    try:
        start_time = time.time()
        is_math, conf_doc, math_basis = _detect_mathematical_reasoning(dummy_func)
        end_time = time.time()

        # Should complete quickly even with large input
        execution_time = end_time - start_time
        if execution_time > 1.0:  # Should be much faster
            print(f"❌ ReDoS protection FAILED: took {execution_time:.2f}s")
            return False
        else:
            print(f"✅ ReDoS protection PASSED: executed in {execution_time:.3f}s")
            return True
    finally:
        inspect.getsource = original_getsource

def test_prototype_pollution_protection():
    """Test prototype pollution vulnerability protection."""
    print("🔍 Testing prototype pollution protection...")

    # Malicious tool spec attempting prototype pollution
    malicious_spec = {
        "type": "function",
        "function": {
            "name": "test_func",
            "description": "A test function",
            "parameters": {"type": "object"}
        },
        "__proto__": {"malicious": "payload"},
        "constructor": {"prototype": {"polluted": True}},
        "forbidden_key": "should_be_filtered"
    }

    try:
        safe_spec = _safe_copy_spec(malicious_spec)

        # Check that malicious keys were filtered out
        forbidden_keys = ["__proto__", "constructor", "forbidden_key"]
        found_forbidden = [key for key in forbidden_keys if key in safe_spec]

        if found_forbidden:
            print(f"❌ Prototype pollution protection FAILED: found forbidden keys {found_forbidden}")
            return False

        # Check that legitimate keys were preserved
        if safe_spec.get("type") != "function":
            print("❌ Prototype pollution protection FAILED: legitimate keys lost")
            return False

        if "name" not in safe_spec.get("function", {}):
            print("❌ Prototype pollution protection FAILED: function keys lost")
            return False

        print("✅ Prototype pollution protection PASSED: malicious keys filtered, legitimate keys preserved")
        return True

    except Exception as e:
        print(f"❌ Prototype pollution protection FAILED with exception: {e}")
        return False

def test_code_exposure_protection():
    """Test code exposure vulnerability protection."""
    print("🔍 Testing code exposure protection...")

    # Test with lambda function (should trigger TypeError)
    lambda_func = lambda x: x * 2

    # Test with built-in function (should trigger OSError)
    builtin_func = print

    # Test with dynamic function (no __code__ attribute)
    class DynamicFunc:
        def __call__(self):
            pass

    dynamic_func = DynamicFunc()

    test_cases = [
        ("lambda function", lambda_func),
        ("builtin function", builtin_func),
        ("dynamic function", dynamic_func)
    ]

    for test_name, test_func in test_cases:
        try:
            is_math, conf_doc, math_basis = _detect_mathematical_reasoning(test_func)
            print(f"✅ Code exposure protection PASSED for {test_name}: no exception raised")
        except Exception as e:
            print(f"❌ Code exposure protection FAILED for {test_name}: {e}")
            return False

    return True

def test_platform_format_security():
    """Test that platform format adapters use secure copying."""
    print("🔍 Testing platform format security...")

    malicious_spec = {
        "type": "function",
        "function": {
            "name": "test_func",
            "description": "A test function",
            "parameters": {"type": "object"}
        },
        "__proto__": {"malicious": "payload"}
    }

    try:
        # Test OpenAI format
        openai_spec = _openai_format(malicious_spec)
        if "__proto__" in openai_spec:
            print("❌ OpenAI format security FAILED: malicious keys present")
            return False

        # Test Bedrock format
        bedrock_spec = _bedrock_format(malicious_spec)
        if "__proto__" in bedrock_spec:
            print("❌ Bedrock format security FAILED: malicious keys present")
            return False

        print("✅ Platform format security PASSED: both OpenAI and Bedrock formats secure")
        return True

    except Exception as e:
        print(f"❌ Platform format security FAILED with exception: {e}")
        return False

def test_backward_compatibility():
    """Test that security fixes maintain backward compatibility."""
    print("🔍 Testing backward compatibility...")

    # Create a valid tool spec
    valid_spec = {
        "type": "function",
        "function": {
            "name": "valid_func",
            "description": "A valid function",
            "parameters": {
                "type": "object",
                "properties": {
                    "param1": {"type": "string"}
                },
                "required": ["param1"]
            }
        }
    }

    try:
        # Test that all functions still work with valid input
        safe_spec = _safe_copy_spec(valid_spec)
        openai_spec = _openai_format(valid_spec)
        bedrock_spec = _bedrock_format(valid_spec)

        # Verify structure is preserved
        assert safe_spec["function"]["name"] == "valid_func"
        assert openai_spec["function"]["name"] == "valid_func"
        assert bedrock_spec["toolSpec"]["name"] == "valid_func"

        print("✅ Backward compatibility PASSED: all functions work with valid input")
        return True

    except Exception as e:
        print(f"❌ Backward compatibility FAILED: {e}")
        return False

def main():
    """Run all security tests."""
    print("🚨 SECURITY VULNERABILITY RE-VERIFICATION TEST SUITE")
    print("=" * 60)

    tests = [
        ("ReDoS Protection", test_redos_protection),
        ("Prototype Pollution Protection", test_prototype_pollution_protection),
        ("Code Exposure Protection", test_code_exposure_protection),
        ("Platform Format Security", test_platform_format_security),
        ("Backward Compatibility", test_backward_compatibility)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        result = test_func()
        results.append((test_name, result))

    print("\n" + "=" * 60)
    print("🎯 SECURITY TEST RESULTS:")

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL SECURITY TESTS PASSED - VULNERABILITIES SUCCESSFULLY FIXED!")
        return 0
    else:
        print("🚨 SECURITY TESTS FAILED - VULNERABILITIES STILL PRESENT!")
        return 1

if __name__ == "__main__":
    sys.exit(main())