#!/usr/bin/env python3
"""
Test script to verify that safe metadata is still properly exposed.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from reasoning_library.exceptions import ReasoningError

def test_safe_metadata_exposure():
    """Test that safe metadata is still properly exposed."""

    print("=== SAFE METADATA EXPOSURE TEST ===")

    # Test with safe metadata only
    safe_details = {
        "error_code": 400,
        "validation_type": "input_validation",
        "operation": "user_registration",
        "category": "authentication",
    }

    error = ReasoningError("Validation failed", safe_details)
    error_message = str(error)

    print(f"Error message: {error_message}")

    # Check that safe metadata is exposed
    expected_metadata = ["error_code: 400", "validation_type: input_validation", "operation: user_registration", "category: authentication"]

    for metadata in expected_metadata:
        if metadata in error_message:
            print(f"✅ Safe metadata exposed: {metadata}")
        else:
            print(f"❌ Safe metadata missing: {metadata}")
            return False

    # Test with mixed safe and sensitive data
    mixed_details = {
        "error_code": 500,
        "api_key": "secret_key_123",  # This should NOT be exposed
        "validation_type": "format_check",
        "password": "user_password_456",  # This should NOT be exposed
    }

    error2 = ReasoningError("Processing error", mixed_details)
    error2_message = str(error2)

    print(f"\nMixed data error message: {error2_message}")

    # Check that only safe data is exposed
    if "error_code: 500" in error2_message:
        print("✅ Safe error_code exposed")
    else:
        print("❌ Safe error_code missing")
        return False

    if "validation_type: format_check" in error2_message:
        print("✅ Safe validation_type exposed")
    else:
        print("❌ Safe validation_type missing")
        return False

    # Check that sensitive data is NOT exposed
    if "secret_key_123" not in error2_message:
        print("✅ Sensitive API key properly hidden")
    else:
        print("❌ Sensitive API key exposed!")
        return False

    if "user_password_456" not in error2_message:
        print("✅ Sensitive password properly hidden")
    else:
        print("❌ Sensitive password exposed!")
        return False

    # Test debug functionality
    debug_info = error2.get_debug_info(include_sensitive=True)
    if "secret_key_123" in debug_info:
        print("✅ Debug mode exposes sensitive data when requested")
    else:
        print("❌ Debug mode doesn't expose sensitive data")
        return False

    safe_debug_info = error2.get_debug_info(include_sensitive=False)
    if "secret_key_123" not in safe_debug_info:
        print("✅ Safe debug mode doesn't expose sensitive data")
    else:
        print("❌ Safe debug mode exposes sensitive data")
        return False

    return True

if __name__ == "__main__":
    if test_safe_metadata_exposure():
        print("\n✅ ALL TESTS PASSED - Safe metadata properly exposed")
        sys.exit(0)
    else:
        print("\n❌ TESTS FAILED - Safe metadata not working correctly")
        sys.exit(1)