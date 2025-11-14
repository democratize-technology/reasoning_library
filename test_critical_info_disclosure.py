#!/usr/bin/env python3
"""
Test script to demonstrate the critical information disclosure vulnerability.

This script shows how sensitive data can be leaked through exception __str__ method.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from reasoning_library.exceptions import ReasoningError

def test_information_disclosure_vulnerability():
    """Demonstrate the critical information disclosure vulnerability."""

    print("=== CRITICAL INFORMATION DISCLOSURE VULNERABILITY TEST ===")

    # Simulate sensitive data that should not be exposed
    sensitive_data = {
        "api_key": "sk-1234567890abcdef",  # API key that should be secret
        "database_connection": "postgresql://user:password@internal-db.company.com:5432/secrets",
        "file_path": "/etc/passwd",  # System file path
        "internal_ip": "192.168.1.100",  # Internal network information
        "user_session": "abc123xyz789session",  # Session token
        "encryption_key": "my_secret_encryption_key_123",  # Cryptographic key
    }

    # Create an exception with sensitive details
    error = ReasoningError("Validation failed", sensitive_data)

    # This demonstrates how the vulnerability exposes sensitive data
    error_message = str(error)
    print(f"Error message: {error_message}")

    # Check if sensitive data is exposed
    sensitive_exposed = []

    if "sk-1234567890abcdef" in error_message:
        sensitive_exposed.append("API KEY")

    if "password" in error_message.lower():
        sensitive_exposed.append("DATABASE PASSWORD")

    if "/etc/passwd" in error_message:
        sensitive_exposed.append("SYSTEM FILE PATH")

    if "192.168.1.100" in error_message:
        sensitive_exposed.append("INTERNAL IP ADDRESS")

    if "abc123xyz789session" in error_message:
        sensitive_exposed.append("SESSION TOKEN")

    if "my_secret_encryption_key_123" in error_message:
        sensitive_exposed.append("ENCRYPTION KEY")

    print(f"\n🚨 VULNERABILITY CONFIRMED:")
    print(f"   Sensitive data exposed: {sensitive_exposed}")
    print(f"   Total sensitive items leaked: {len(sensitive_exposed)}")

    if sensitive_exposed:
        print("\n❌ CRITICAL: This vulnerability allows attackers to:")
        print("   - Steal API keys and credentials")
        print("   - Access internal system information")
        print("   - Bypass security controls")
        print("   - Gain unauthorized access to systems")
        return False
    else:
        print("\n✅ No sensitive data detected in error message")
        return True

def test_attacker_scenario():
    """Simulate how an attacker could exploit this vulnerability."""

    print("\n=== ATTACKER SCENARIO SIMULATION ===")

    # Attacker-controlled input that could trigger exception
    user_input = {
        "malicious_payload": {"secret": "admin_password_123"},
        "injected_data": {"internal_config": "super_secret_value"}
    }

    try:
        # Simulate application code that raises exception with user data
        raise ReasoningError("Processing failed", user_input)
    except Exception as e:
        error_output = str(e)
        print(f"Exception output that attacker sees: {error_output}")

        # Attacker can now extract sensitive information
        if "admin_password_123" in error_output:
            print("🚨 ATTACKER SUCCESS: Extracted admin password!")

        if "super_secret_value" in error_output:
            print("🚨 ATTACKER SUCCESS: Extracted internal config!")

if __name__ == "__main__":
    # Test the vulnerability
    is_safe = test_information_disclosure_vulnerability()
    test_attacker_scenario()

    if not is_safe:
        print("\n" + "="*60)
        print("🔴 CRITICAL SECURITY VULNERABILITY CONFIRMED!")
        print("   Exception __str__ method exposes sensitive details")
        print("   This allows information disclosure attacks")
        print("="*60)
        sys.exit(1)
    else:
        print("\n✅ Security test passed - no information disclosure detected")
        sys.exit(0)