#!/usr/bin/env python3
"""
Simple test to verify the exception security fix works correctly.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from reasoning_library.exceptions import ReasoningError, ValidationError

def test_exception_security_fix():
    """Test that the exception security fix works correctly."""

    print("=== EXCEPTION SECURITY FIX TEST ===")

    # Test 1: Basic exception without details
    error1 = ReasoningError("Basic error")
    assert str(error1) == "Basic error"
    print("✅ Basic exception works")

    # Test 2: Exception with safe metadata
    error2 = ReasoningError("Safe error", {
        "error_code": 400,
        "validation_type": "input_check",
        "operation": "auth"
    })
    error2_str = str(error2)
    assert "error_code: 400" in error2_str
    assert "validation_type: input_check" in error2_str
    assert "operation: auth" in error2_str
    assert "Details:" not in error2_str
    print("✅ Safe metadata exposed correctly")

    # Test 3: Exception with sensitive data (should be protected)
    error3 = ReasoningError("Sensitive error", {
        "api_key": "secret_key_123",
        "password": "secret_pass_456",
        "database_url": "postgres://user:pass@host/db",
        "error_code": 500  # This should still be exposed
    })
    error3_str = str(error3)

    # Verify sensitive data is NOT exposed
    assert "secret_key_123" not in error3_str
    assert "secret_pass_456" not in error3_str
    assert "postgres://user:pass@host/db" not in error3_str
    assert "Details:" not in error3_str

    # Verify safe data IS exposed
    assert "error_code: 500" in error3_str
    print("✅ Sensitive data properly protected")

    # Test 4: Debug functionality
    debug_info = error3.get_debug_info(include_sensitive=True)
    assert "secret_key_123" in debug_info
    assert "secret_pass_456" in debug_info
    assert "Details:" in debug_info
    print("✅ Debug functionality works with permission")

    # Test 5: Safe debug mode
    safe_debug = error3.get_debug_info(include_sensitive=False)
    assert "secret_key_123" not in safe_debug
    assert "secret_pass_456" not in safe_debug
    print("✅ Safe debug mode protects sensitive data")

    # Test 6: Details property still accessible
    assert error3.details["api_key"] == "secret_key_123"
    assert error3.details["password"] == "secret_pass_456"
    print("✅ Details property still accessible")

    # Test 7: ValidationError inherits secure behavior
    validation_error = ValidationError("Invalid input", {
        "field": "username",
        "value": "admin",
        "security_issue": "This should be hidden"
    })
    validation_str = str(validation_error)
    assert "security_issue" not in validation_str
    assert "Details:" not in validation_str
    print("✅ ValidationError inherits secure behavior")

    return True

def test_backward_compatibility():
    """Test that the fix maintains backward compatibility."""

    print("\n=== BACKWARD COMPATIBILITY TEST ===")

    # Test that existing code patterns still work
    try:
        # Existing exception handling patterns should still work
        try:
            raise ValidationError("Test error", {"code": 123})
        except Exception as e:
            # Should still be catchable as general Exception
            assert isinstance(e, ValidationError)
            assert isinstance(e, ReasoningError)
            assert isinstance(e, Exception)
            assert str(e) == "Test error" or "code:" in str(e)
            print("✅ Exception handling backward compatibility maintained")

        # Test that .details property works
        error = ReasoningError("Test", {"key": "value"})
        assert error.details == {"key": "value"}
        print("✅ Details property backward compatibility maintained")

        # Test that message property works
        assert error.message == "Test"
        print("✅ Message property backward compatibility maintained")

        return True

    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False

if __name__ == "__main__":
    success = True

    try:
        success &= test_exception_security_fix()
        success &= test_backward_compatibility()

        if success:
            print("\n✅ ALL SECURITY FIX TESTS PASSED")
            print("   - Sensitive data is protected from accidental exposure")
            print("   - Safe metadata is still properly exposed")
            print("   - Debug functionality works with explicit permission")
            print("   - Backward compatibility is maintained")
            sys.exit(0)
        else:
            print("\n❌ SOME TESTS FAILED")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)