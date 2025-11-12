#!/usr/bin/env python3
"""
Verification test for the information disclosure fix in code inspection.
This test ensures the fix works and prevents source code exposure.
"""

import sys
import os
import tempfile

# Add src to path for import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from reasoning_library.core import _get_function_source_cached, tool_spec, clear_performance_caches


def test_source_code_inspection_blocked():
    """Test that source code inspection is now blocked for security."""

    print("🛡️ Testing that source code inspection is blocked...")

    # Create a temporary file with sensitive content
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
# This file contains SENSITIVE INFORMATION
SECRET_API_KEY = "sk-secret-key-12345"
DATABASE_PASSWORD = "super-secret-password"

def sensitive_function():
    # This should NOT be accessible through reasoning library
    return SECRET_API_KEY + ":" + DATABASE_PASSWORD
""")
        temp_file_path = f.name

    try:
        # Load the module and create a function that uses sensitive code
        import importlib.util
        spec = importlib.util.spec_from_file_location("sensitive_module", temp_file_path)
        sensitive_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sensitive_module)

        # Try to access source code through the reasoning library
        sensitive_func = sensitive_module.sensitive_function

        print("Attempting to extract source code through reasoning library...")

        # This should now be blocked by the fix
        extracted_source = _get_function_source_cached(sensitive_func)

        print(f"Extracted source code length: {len(extracted_source)} characters")
        print(f"Extracted content: '{extracted_source}'")

        # Check if sensitive information is still being disclosed
        sensitive_indicators = [
            "SECRET_API_KEY",
            "DATABASE_PASSWORD",
            "sk-secret-key-12345",
            "super-secret-password"
        ]

        found_sensitive = []
        for indicator in sensitive_indicators:
            if indicator in extracted_source:
                found_sensitive.append(indicator)

        if found_sensitive:
            print(f"❌ FAIL: Sensitive data still exposed: {found_sensitive}")
            return False
        elif extracted_source == "":
            print("✅ SUCCESS: Source code inspection blocked - empty string returned")
            return True
        else:
            print(f"⚠️  UNEXPECTED: Got non-empty but safe result: '{extracted_source}'")
            return len(extracted_source) == 0  # True only if empty

    except Exception as e:
        print(f"❌ FAIL: Exception during fix verification: {e}")
        return False
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
        except:
            pass


def test_safe_function_inspection_blocked():
    """Test that even safe function inspection is blocked."""

    print("\n🛡️ Testing safe function inspection blocking...")

    # Test with regular functions (should also be blocked for consistency)
    def safe_function(x, y=10):
        """Safe test function."""
        return x + y

    try:
        source = _get_function_source_cached(safe_function)

        if source == "":
            print("✅ SUCCESS: Safe function source also blocked (consistent security)")
            return True
        elif "safe_function" in source and len(source) > 20:
            print(f"❌ FAIL: Safe function source still exposed: {source[:100]}...")
            return False
        else:
            print(f"⚠️  UNEXPECTED: Got unexpected result: '{source}'")
            return False

    except Exception as e:
        print(f"❌ FAIL: Exception with safe function: {e}")
        return False


def test_lambda_function_still_safe():
    """Test that lambda function behavior is consistent."""

    print("\n🛡️ Testing lambda function behavior...")

    # Lambda functions should still return empty string
    lambda_func = lambda x: x * 2

    try:
        source = _get_function_source_cached(lambda_func)

        # Lambda functions should return empty string (now consistent with security fix)
        if source == "":
            print("✅ SUCCESS: Lambda function returns empty string (consistent with security)")
            return True
        else:
            print(f"⚠️  UNEXPECTED: Lambda returned: '{source}'")
            return False  # Should be empty now for consistency

    except Exception as e:
        print(f"❌ FAIL: Exception with lambda function: {e}")
        return False


def test_tool_spec_still_works():
    """Test that tool_spec decorator still works without source code inspection."""

    print("\n🛡️ Testing tool_spec decorator functionality...")

    @tool_spec(
        mathematical_basis="Test function for security testing",
        confidence_factors=["test"]
    )
    def tool_function(data):
        """Tool function for testing."""
        return f"processed: {data}"

    try:
        # The tool_spec decorator should still work even without source inspection
        result = tool_function("test_input")

        print(f"Tool function result: {result}")

        if "processed:" in result:
            print("✅ SUCCESS: Tool function works correctly without source inspection")
            return True
        else:
            print("❌ FAIL: Tool function didn't work as expected")
            return False

    except Exception as e:
        print(f"❌ FAIL: Exception with tool function: {e}")
        return False


def test_cache_behavior_consistent():
    """Test that caching behavior is consistent with the fix."""

    print("\n🛡️ Testing cache behavior consistency...")

    def test_func():
        """Test function for caching."""
        return "test"

    try:
        # First call
        result1 = _get_function_source_cached(test_func)
        # Second call (should use cache)
        result2 = _get_function_source_cached(test_func)

        # Both should be empty strings
        if result1 == "" and result2 == "" and result1 == result2:
            print("✅ SUCCESS: Cache behavior consistent with security fix")
            return True
        else:
            print(f"❌ FAIL: Inconsistent cache results: '{result1}' vs '{result2}'")
            return False

    except Exception as e:
        print(f"❌ FAIL: Exception during cache test: {e}")
        return False


def test_clear_caches_still_works():
    """Test that cache clearing still works with the fix."""

    print("\n🛡️ Testing cache clearing functionality...")

    def clear_test_func():
        """Clear test function."""
        return "clear_test"

    try:
        # Add to cache
        result1 = _get_function_source_cached(clear_test_func)

        # Clear caches
        cleared_stats = clear_performance_caches()

        # Try again
        result2 = _get_function_source_cached(clear_test_func)

        # Both should still be empty strings
        if result1 == "" and result2 == "":
            print("✅ SUCCESS: Cache clearing works with security fix")
            print(f"   Cache clear stats: {cleared_stats}")
            return True
        else:
            print(f"❌ FAIL: Cache clearing broke functionality")
            return False

    except Exception as e:
        print(f"❌ FAIL: Exception during cache clearing test: {e}")
        return False


if __name__ == "__main__":
    print("🛡️ INFORMATION DISCLOSURE FIX VERIFICATION TEST")
    print("=" * 60)
    print("Testing that the information disclosure vulnerability is fixed")
    print("=" * 60)

    all_passed = True

    # Test 1: Source code inspection blocked
    print("TEST 1: Source Code Inspection Blocked")
    print("-" * 40)
    all_passed &= test_source_code_inspection_blocked()

    # Test 2: Safe function inspection blocked
    print("\nTEST 2: Safe Function Inspection Blocked")
    print("-" * 40)
    all_passed &= test_safe_function_inspection_blocked()

    # Test 3: Lambda function consistency
    print("\nTEST 3: Lambda Function Consistency")
    print("-" * 40)
    all_passed &= test_lambda_function_still_safe()

    # Test 4: Tool spec still works
    print("\nTEST 4: Tool Spec Functionality")
    print("-" * 40)
    all_passed &= test_tool_spec_still_works()

    # Test 5: Cache behavior consistency
    print("\nTEST 5: Cache Behavior Consistency")
    print("-" * 40)
    all_passed &= test_cache_behavior_consistent()

    # Test 6: Cache clearing still works
    print("\nTEST 6: Cache Clearing Functionality")
    print("-" * 40)
    all_passed &= test_clear_caches_still_works()

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("🎉 Information disclosure vulnerability fixed successfully!")
        print("🛡️ Source code inspection disabled for security")
        print("⚡ All functionality preserved")
        print("🔒 No sensitive information can be extracted")
    else:
        print("❌ SOME TESTS FAILED")
        print("🚨 Information disclosure fix may need adjustment")

    print("=" * 60)

    sys.exit(0 if all_passed else 1)