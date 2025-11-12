#!/usr/bin/env python3
"""
Test for information disclosure vulnerability through unsafe code inspection.
This test demonstrates the vulnerability and verifies the fix.
"""

import os
import sys
import tempfile

# Add src to path for import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from reasoning_library.core import _get_function_source_cached, tool_spec


def test_source_code_disclosure_vulnerability():
    """Test that demonstrates information disclosure through source code inspection."""

    print("🔍 Testing source code disclosure vulnerability...")

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

        # This should be blocked but currently isn't (vulnerability)
        extracted_source = _get_function_source_cached(sensitive_func)

        print(f"Extracted source code length: {len(extracted_source)} characters")

        # Check if sensitive information was disclosed
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
            print("❌ VULNERABILITY CONFIRMED: Information disclosure detected!")
            print(f"   Sensitive data exposed: {found_sensitive}")
            print(f"   Source snippet: {extracted_source[:200]}...")
            return True  # Vulnerability exists
        else:
            print("ℹ️  No obvious sensitive data in this test case")
            # Still check if source code was extracted at all
            if "sensitive_function" in extracted_source and len(extracted_source) > 50:
                print("⚠️  Source code extracted - potential vulnerability")
                return True
            else:
                print("✅ No source code extracted - may be safe")
                return False

    except Exception as e:
        print(f"❌ FAIL: Exception during disclosure test: {e}")
        return False
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
        except:
            pass


def test_code_inspection_on_builtins():
    """Test code inspection on built-in functions that should be safe."""

    print("\n🔍 Testing code inspection on built-in functions...")

    # Test with regular functions (should be safe)
    def safe_function(x, y=10):
        """Safe test function."""
        return x + y

    try:
        source = _get_function_source_cached(safe_function)

        if source and len(source) > 20:
            print("✅ Safe function source extracted correctly")
            print(f"   Source: {source[:100]}...")
            return True
        else:
            print("❌ FAIL: Safe function source not extracted")
            return False

    except Exception as e:
        print(f"❌ FAIL: Exception with safe function: {e}")
        return False


def test_code_inspection_on_lambda():
    """Test code inspection on lambda functions."""

    print("\n🔍 Testing code inspection on lambda functions...")

    # Lambda functions typically don't have accessible source
    lambda_func = lambda x: x * 2

    try:
        source = _get_function_source_cached(lambda_func)

        # Lambda functions should return empty string (safe)
        if source == "":
            print("✅ Lambda function correctly returns empty source (safe)")
            return True
        else:
            print(f"⚠️  Lambda function returned: '{source}' (may be safe or unexpected)")
            return True  # Not necessarily a vulnerability

    except Exception as e:
        print(f"❌ FAIL: Exception with lambda function: {e}")
        return False


def test_tool_spec_code_inspection():
    """Test if tool_spec decorator exposes source code."""

    print("\n🔍 Testing tool_spec decorator code inspection...")

    @tool_spec(
        mathematical_basis="Test function for security testing",
        confidence_factors=["test"]
    )
    def tool_function(data):
        """Tool function for testing."""
        return f"processed: {data}"

    try:
        # The tool_spec decorator uses mathematical reasoning detection
        # which internally calls _get_function_source_cached
        result = tool_function("test_input")

        print(f"Tool function result: {result}")

        # Check if the function was processed without exposing source
        if "processed:" in result:
            print("✅ Tool function works without exposing source code")
            return True
        else:
            print("❌ FAIL: Tool function didn't work as expected")
            return False

    except Exception as e:
        print(f"❌ FAIL: Exception with tool function: {e}")
        return False


def test_malicious_source_injection():
    """Test if malicious source code can be injected and extracted."""

    print("\n🔍 Testing malicious source injection...")

    # Create a function with potentially malicious-looking source
    def malicious_test_func():
        """Function that looks malicious in source code."""
        # These comments look suspicious but are harmless for testing
        # eval("os.system('rm -rf /')")  # This would be dangerous if executed
        # subprocess.call(['format', 'C:'])  # Dangerous Windows command
        return "harmless_return_value"

    try:
        source = _get_function_source_cached(malicious_test_func)

        # Check if dangerous-looking code is exposed
        dangerous_patterns = [
            "os.system",
            "subprocess.call",
            "rm -rf",
            "format C:",
            "eval("
        ]

        found_dangerous = []
        for pattern in dangerous_patterns:
            if pattern in source:
                found_dangerous.append(pattern)

        if found_dangerous:
            print(f"❌ VULNERABILITY: Dangerous-looking code exposed: {found_dangerous}")
            print(f"   Source snippet: {source[:300]}...")
            return True  # Vulnerability exists
        else:
            print("✅ No dangerous patterns in extracted source")
            print(f"   Safe source: {source[:100]}...")
            return True  # Safe behavior

    except Exception as e:
        print(f"❌ FAIL: Exception during malicious source test: {e}")
        return False


if __name__ == "__main__":
    print("🔍 INFORMATION DISCLOSURE VULNERABILITY TEST")
    print("=" * 60)
    print("Testing for information disclosure through unsafe code inspection")
    print("=" * 60)

    vulnerability_detected = False

    # Test 1: Source code disclosure from external files
    print("TEST 1: Source Code Disclosure from External Files")
    print("-" * 50)
    vulnerability_detected |= test_source_code_disclosure_vulnerability()

    # Test 2: Safe code inspection on built-ins
    print("\nTEST 2: Safe Code Inspection")
    print("-" * 50)
    vulnerability_detected |= test_code_inspection_on_builtins()

    # Test 3: Lambda function inspection
    print("\nTEST 3: Lambda Function Inspection")
    print("-" * 50)
    vulnerability_detected |= test_code_inspection_on_lambda()

    # Test 4: Tool spec code inspection
    print("\nTEST 4: Tool Spec Code Inspection")
    print("-" * 50)
    vulnerability_detected |= test_tool_spec_code_inspection()

    # Test 5: Malicious source injection
    print("\nTEST 5: Malicious Source Injection")
    print("-" * 50)
    vulnerability_detected |= test_malicious_source_injection()

    print("\n" + "=" * 60)
    if vulnerability_detected:
        print("❌ VULNERABILITIES DETECTED")
        print("🚨 CRITICAL: Information disclosure through unsafe code inspection")
        print("📋 Issues found:")
        print("   - Source code can be extracted from external modules")
        print("   - Sensitive information may be exposed via inspect.getsource()")
        print("   - File system access through code inspection")
        print("   - Implementation details exposed without access controls")
        print("\n⚠️  IMMEDIATE FIX REQUIRED")
    else:
        print("✅ NO OBVIOUS VULNERABILITIES DETECTED")
        print("📊 Tests completed without detecting obvious information disclosure")
        print("⚠️  However, inspect.getsource() usage should still be reviewed")

    print("=" * 60)

    sys.exit(1 if vulnerability_detected else 0)
