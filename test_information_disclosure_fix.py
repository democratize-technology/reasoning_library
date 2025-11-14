#!/usr/bin/env python3
"""
Test for Information Disclosure Security Fix (ID-001)

This test verifies that the security fix for information disclosure
vulnerability is working correctly. The fix ensures that:

1. No stack traces are exposed in logs
2. No file paths are exposed in logs
3. No user directory paths are exposed in logs
4. Exception information is properly sanitized
5. Useful debugging information is still available to developers
"""

import logging
import io
from contextlib import redirect_stderr
from typing import Any

# Import the fixed function
from src.reasoning_library.null_handling import with_null_safety, _sanitize_exception_message


def test_secure_exception_sanitization():
    """Test that the _sanitize_exception_message function properly sanitizes sensitive data."""
    print("=== TESTING EXCEPTION MESSAGE SANITIZATION ===")

    test_cases = [
        # (function_name, exception_type, exception_message, expected_sanitizations)
        ("test_func", "KeyError", "'missing_key'", {"should_contain": ["test_func", "KeyError", "missing_key"]}),
        ("process_data", "FileNotFoundError", "/Users/john/secrets.txt", {"should_not_contain": ["/Users/john"], "should_contain": ["[USER_DIR]", "[FILE]"]}),
        ("network_call", "ConnectionError", "Failed to connect to 192.168.1.100:8080", {"should_not_contain": ["192.168.1.100"], "should_contain": ["[IP]"]}),
        ("auth_func", "ValueError", "Invalid password='superSecretPassword123'", {"should_not_contain": ["superSecretPassword123"], "should_contain": ["[REDACTED]"]}),
        ("config_loader", "TypeError", "Cannot load /opt/app/config.py: invalid syntax", {"should_not_contain": ["/opt/app/config.py"], "should_contain": ["[FILE]"]}),
        ("long_message", "RuntimeError", "A" * 300, {"should_contain": ["[TRUNCATED]"]}),
    ]

    all_passed = True

    for func_name, exception_type, exception_msg, expectations in test_cases:
        sanitized = _sanitize_exception_message(func_name, exception_type, exception_msg)
        print(f"\nOriginal: {exception_msg}")
        print(f"Sanitized: {sanitized}")

        # Check that function name and exception type are preserved
        if func_name not in sanitized:
            print(f"❌ FAILED: Function name '{func_name}' not preserved")
            all_passed = False

        if exception_type not in sanitized:
            print(f"❌ FAILED: Exception type '{exception_type}' not preserved")
            all_passed = False

        # Check expectations
        if "should_contain" in expectations:
            for expected in expectations["should_contain"]:
                if expected not in sanitized:
                    print(f"❌ FAILED: Expected '{expected}' not found in sanitized message")
                    all_passed = False
                else:
                    print(f"✅ PASSED: '{expected}' properly handled")

        if "should_not_contain" in expectations:
            for not_expected in expectations["should_not_contain"]:
                if not_expected in sanitized:
                    print(f"❌ FAILED: Sensitive data '{not_expected}' not properly removed")
                    all_passed = False
                else:
                    print(f"✅ PASSED: Sensitive data properly removed")

    return all_passed


def test_secure_logging_no_information_disclosure():
    """Test that the fixed logging does not disclose sensitive information."""
    print("\n=== TESTING SECURE LOGGING BEHAVIOR ===")

    # Capture stderr output to verify no information disclosure
    stderr_capture = io.StringIO()

    # Configure logging BEFORE redirecting stderr
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')

    with redirect_stderr(stderr_capture):
        # Create a function that will trigger a business exception
        @with_null_safety(expected_return_type=str)
        def secure_function():
            # This will trigger a KeyError which is now caught and logged securely
            data = {"key": "value"}
            return data["missing_key"]  # KeyError (business logic error)

        # Call the function to trigger the secure logging
        result = secure_function()

    # Get the captured stderr output
    stderr_output = stderr_capture.getvalue()

    print(f"Function result: {result}")
    print(f"Captured log output: {stderr_output}")

    # Check for information disclosure
    vulnerabilities_found = []

    if "Traceback (most recent call last):" in stderr_output:
        vulnerabilities_found.append("Full stack trace exposed")

    if "src/reasoning_library" in stderr_output:
        vulnerabilities_found.append("System file paths exposed")

    if "Users/eringreen/Development" in stderr_output:
        vulnerabilities_found.append("User directory paths exposed")

    if ".py:" in stderr_output:  # Line number references
        vulnerabilities_found.append("Source file line numbers exposed")

    print(f"\n=== SECURITY ANALYSIS ===")
    if vulnerabilities_found:
        print("❌ SECURITY ISSUES FOUND:")
        for issue in vulnerabilities_found:
            print(f"  - {issue}")
        return False
    else:
        print("✅ NO INFORMATION DISCLOSURE DETECTED")
        print("✅ Exception logging is now secure")
        return True


def test_still_useful_for_debugging():
    """Test that sanitized logs are still useful for debugging."""
    print("\n=== TESTING DEBUGGING UTILITY ===")

    # Configure logging BEFORE redirecting stderr
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')

    stderr_capture = io.StringIO()

    with redirect_stderr(stderr_capture):

        @with_null_safety(expected_return_type=str)
        def debug_test_function():
            # Different types of business exceptions
            test_cases = [
                lambda: {}["missing_key"],  # KeyError
                lambda: int("not_a_number"),  # ValueError
                lambda: "string" + 123,  # TypeError
            ]

            # Just run the first one for this test
            return test_cases[0]()

        result = debug_test_function()

    stderr_output = stderr_capture.getvalue()

    # Check that useful debugging information is preserved
    useful_info_found = []

    if "Business exception handled" in stderr_output:
        useful_info_found.append("Exception handling status")

    if "debug_test_function" in stderr_output:
        useful_info_found.append("Function name preserved")

    if "KeyError" in stderr_output:
        useful_info_found.append("Exception type preserved")

    if "missing_key" in stderr_output:
        useful_info_found.append("Relevant exception details preserved")

    print(f"Full log output for debugging: '{stderr_output}'")
    print(f"Debugging utility: {len(useful_info_found)}/4 useful elements preserved")

    for info in useful_info_found:
        print(f"✅ {info}")

    # Debug each check
    print(f"Contains 'Business exception handled': {'Business exception handled' in stderr_output}")
    print(f"Contains 'debug_test_function': {'debug_test_function' in stderr_output}")
    print(f"Contains 'KeyError': {'KeyError' in stderr_output}")
    print(f"Contains 'missing_key': {'missing_key' in stderr_output}")

    return len(useful_info_found) >= 3  # At least 3 out of 4 useful elements


def test_regression_no_functional_changes():
    """Test that the security fix doesn't break existing functionality."""
    print("\n=== TESTING FUNCTIONAL REGRESSION ===")

    # Test that the decorator still works as expected
    @with_null_safety(expected_return_type=str)
    def normal_function():
        return "normal result"

    @with_null_safety(expected_return_type=str)
    def exception_function():
        raise KeyError("test error")

    @with_null_safety(expected_return_type=int)
    def return_type_function():
        raise ValueError("type test")

    # Test normal operation
    try:
        result1 = normal_function()
        assert result1 == "normal result"
        print("✅ Normal function execution works")
    except Exception as e:
        print(f"❌ Normal function failed: {e}")
        return False

    # Test exception handling - should return appropriate empty value
    try:
        result2 = exception_function()
        assert result2 == ""  # EMPTY_STRING for str return type
        print("✅ Exception handling works (returns empty string)")
    except Exception as e:
        print(f"❌ Exception handling failed: {e}")
        return False

    # Test different return types
    try:
        result3 = return_type_function()
        assert result3 is None  # NO_VALUE for int return type
        print("✅ Different return types work")
    except Exception as e:
        print(f"❌ Return type handling failed: {e}")
        return False

    return True


if __name__ == "__main__":
    print("🔒 INFORMATION DISCLOSURE SECURITY FIX VERIFICATION")
    print("=" * 60)

    # Run all security tests
    test1_passed = test_secure_exception_sanitization()
    test2_passed = test_secure_logging_no_information_disclosure()
    test3_passed = test_still_useful_for_debugging()
    test4_passed = test_regression_no_functional_changes()

    print(f"\n" + "=" * 60)
    print("=== SECURITY FIX VERIFICATION RESULTS ===")
    print(f"Exception sanitization: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"No information disclosure: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"Debugging utility preserved: {'✅ PASSED' if test3_passed else '❌ FAILED'}")
    print(f"No functional regression: {'✅ PASSED' if test4_passed else '❌ FAILED'}")

    all_tests_passed = all([test1_passed, test2_passed, test3_passed, test4_passed])

    if all_tests_passed:
        print(f"\n🎉 ALL SECURITY TESTS PASSED!")
        print("✅ Information disclosure vulnerability has been successfully fixed")
        print("✅ Exception logging is now secure and production-ready")
        exit(0)
    else:
        print(f"\n⚠️  SOME TESTS FAILED!")
        print("❌ Security fix requires additional work")
        exit(1)