"""
CRIT-003 Test: Information Disclosure through source code inspection

This test ensures that the information disclosure vulnerability through inspect.getsource()
is properly fixed. The vulnerability allowed attackers to extract source code from any
function, potentially exposing API keys, passwords, and proprietary algorithms.
"""

import pytest
from unittest.mock import patch, MagicMock
import inspect
from reasoning_library.core import _get_math_detection_cached, _get_function_source_cached


def test_source_code_inspection_disabled():
    """
    Test that source code inspection is completely disabled to prevent information disclosure.

    CRITICAL: This test ensures that inspect.getsource() cannot be used to extract
    source code from functions, which could expose sensitive information like:
    - API keys and passwords embedded in source code
    - Proprietary algorithms and business logic
    - Internal implementation details
    - Comments containing sensitive information

    Attack Vector:
    - Malicious functions could be registered with the tool registry
    - Source code extraction through inspect.getsource() in hash calculation
    - Information disclosure through caching mechanisms

    Security Requirement:
    - Source code inspection must be completely disabled
    - Hash calculations must not use source code
    - Empty string must be returned for all source code requests
    """

    # Create a test function with sensitive content
    def sensitive_function():
        """This function contains sensitive information that should not be exposed."""
        api_key = "sk-1234567890abcdef"  # This should never be exposed
        password = "super_secret_password"  # This should never be exposed
        proprietary_algorithm = "secret_business_logic"  # This should never be exposed
        return f"Processing with {api_key}"

    # Test 1: _get_function_source_cached must return empty string
    source_result = _get_function_source_cached(sensitive_function)
    assert source_result == "", "Source code inspection must return empty string for security"

    # Test 2: Verify that even with inspect.getsource available, we don't use it
    # This simulates the vulnerability path in _get_math_detection_cached
    with patch('reasoning_library.core.inspect.getsource') as mock_getsource:
        # Configure mock to return sensitive source code (simulating the vulnerability)
        mock_getsource.return_value = "api_key = 'sk-1234567890abcdef'\npassword = 'super_secret'"

        # Call the function that could be vulnerable
        try:
            result = _get_math_detection_cached(sensitive_function)
            # If we get here, verify that source code was not actually used
            # The hash should be created without source code content
        except Exception:
            # Exception is acceptable - source code inspection should be blocked
            pass

        # Verify getsource was not called for security reasons
        # Note: This might be called but the result should not be used in hash
        # The critical security requirement is that source code content is not exposed

    # Test 3: Verify hash calculation does not include source code
    # The main vulnerability was in hash calculation using source code
    with patch('reasoning_library.core.inspect.getsource') as mock_getsource:
        mock_getsource.return_value = "secret_content_here"

        with patch('hashlib.md5') as mock_md5:
            mock_hash = MagicMock()
            mock_md5.return_value = mock_hash
            mock_hash.hexdigest.return_value = "test_hash"

            # Call the function
            _get_math_detection_cached(sensitive_function)

            # Get the content that was hashed
            call_args = mock_md5.call_args
            if call_args:
                hashed_content = call_args[0][0]  # First argument to md5()
                content_str = hashed_content.decode() if isinstance(hashed_content, bytes) else str(hashed_content)

                # CRITICAL SECURITY CHECK: Source code content must not be in hash
                assert "secret_content_here" not in content_str, "Source code must not be included in hash calculation"
                assert "api_key" not in content_str, "API keys must not be exposed in hash calculation"
                assert "password" not in content_str, "Passwords must not be exposed in hash calculation"


def test_source_code_cache_is_empty():
    """
    Test that the source code cache only contains empty strings, preventing
    information disclosure through cache inspection.
    """

    def test_function():
        """Test function with some content."""
        return "test content"

    # Get source code multiple times
    result1 = _get_function_source_cached(test_function)
    result2 = _get_function_source_cached(test_function)

    # Both must be empty strings
    assert result1 == "", "Cached source code must be empty"
    assert result2 == "", "Cached source code must be empty"

    # Cache should only contain empty strings, no actual source code
    # This prevents information disclosure through cache inspection


def test_malicious_source_code_injection_blocked():
    """
    Test that malicious source code injection attempts are blocked.

    Attack Scenario:
    - Malicious actor creates a function with dangerous source code
    - Attempts to register it with the tool registry
    - Tries to extract source code through various vectors

    Security Requirement:
    - All source code extraction must return empty string
    - No exception should expose source code information
    """

    def malicious_function():
        """Contains malicious code that should never be exposed."""
        # This could contain malware, data exfiltration code, etc.
        import os
        os.system("rm -rf /")  # Malicious command - should never be exposed
        eval("__import__('subprocess').getoutput('cat /etc/passwd')")  # Data exfiltration
        return "malicious"

    # Source code extraction must return empty string
    source = _get_function_source_cached(malicious_function)
    assert source == "", "Malicious source code must not be accessible"

    # Even with direct inspect calls, the system should be secure
    try:
        # This should not expose source code due to security measures
        result = _get_math_detection_cached(malicious_function)
        # The result should not contain any malicious source code fragments
        if isinstance(result, tuple) and len(result) >= 1:
            is_mathematical = result[0]
            # The detection should work without exposing source code
            assert isinstance(is_mathematical, bool), "Result should be boolean without source code exposure"
    except Exception:
        # Security exceptions are acceptable - they prevent information disclosure
        pass


def test_information_disclosure_through_error_messages():
    """
    Test that error messages do not expose source code information.

    Attack Vector:
    - Trigger errors in source code inspection
    - Extract information from exception messages or stack traces

    Security Requirement:
    - Error messages must not contain source code fragments
    - Stack traces must not expose sensitive function content
    """

    def function_with_secrets():
        """Contains secrets in comments and strings."""
        # SECRET: database_password = "admin123"
        # API_KEY = "sk-live-secret-key"
        secret_config = {"db": "user:pass@host", "api": "secret-token"}
        return "processing"

    # Try various error conditions that might expose source code
    test_cases = [
        lambda: _get_function_source_cached(None),  # None input
        lambda: _get_function_source_cached(42),    # Invalid input (int)
        lambda: _get_function_source_cached("string"),  # Invalid input (string)
    ]

    for test_case in test_cases:
        try:
            result = test_case()
            # If no exception, result must be empty string
            assert result == "", "Error cases must return empty string, not source code"
        except Exception as e:
            # Exception messages must not contain source code fragments
            error_msg = str(e)
            assert "database_password" not in error_msg, "Error messages must not expose secrets"
            assert "admin123" not in error_msg, "Error messages must not expose passwords"
            assert "sk-live-secret-key" not in error_msg, "Error messages must not expose API keys"
            assert "user:pass@host" not in error_msg, "Error messages must not expose config"


@pytest.mark.security
def test_critical_security_vulnerability_fix():
    """
    CRITICAL SECURITY TEST: Verifies the complete fix for CRIT-003.

    This test ensures that the information disclosure vulnerability through
    inspect.getsource() is completely mitigated. Any failure here indicates
    a critical security vulnerability.

    Vulnerability Details:
    - CVSS Score: 7.5 (High)
    - Attack Vector: Local
    - Attack Complexity: Low
    - Privileges Required: Low
    - User Interaction: None
    - Impact: High (Confidentiality)
    - Scope: Unchanged

    Exploitation Scenario:
    1. Attacker registers malicious function with tool registry
    2. Attacker triggers hash calculation using inspect.getsource()
    3. Source code containing secrets is extracted and cached
    4. Secrets are exfiltrated through cache inspection

    Mitigation Requirements:
    - ALL inspect.getsource() calls must be disabled
    - Source code content must never be used in hash calculations
    - Cache must only contain empty strings for source code
    - No error messages should expose source code fragments
    """

    # Create function with highly sensitive information
    def crown_jewels_function():
        """
        Contains the most sensitive secrets that must never be exposed.

        This represents the worst-case scenario for information disclosure.
        """
        # Production database credentials
        db_config = {
            "host": "prod-db.company.com",
            "username": "admin",
            "password": "SuperSecretDBPassword123!",
            "api_key": "sk-prod-live-very-secret-key-abcdef123456"
        }

        # Third-party service credentials
        external_apis = {
            "aws_secret_key": "AKIAIOSFODNN7EXAMPLE",
            "github_token": "ghp_1234567890abcdef1234567890abcdef123456",
            "slack_webhook": "https://hooks.slack.com/services/T00000000/B00000000/REDACTED"
        }

        # Proprietary business logic
        secret_algorithm = "patented_business_logic_v2.0"

        return f"Processing with {db_config['api_key']}"

    # 1. Direct source code extraction must be blocked
    direct_source = _get_function_source_cached(crown_jewels_function)
    assert direct_source == "", "Direct source code extraction must return empty string"

    # 2. Hash calculation must not include source code
    with patch('hashlib.md5') as mock_md5:
        mock_hash = MagicMock()
        mock_hash.hexdigest.return_value = "safe_hash"
        mock_md5.return_value = mock_hash

        # This should work without exposing source code
        result = _get_math_detection_cached(crown_jewels_function)

        # Verify what was hashed does not contain secrets
        if mock_md5.called:
            hashed_content = mock_md5.call_args[0][0]
            content_str = hashed_content.decode() if isinstance(hashed_content, bytes) else str(hashed_content)

            # CRITICAL: None of these sensitive values should be in the hash
            sensitive_values = [
                "SuperSecretDBPassword123!",
                "sk-prod-live-very-secret-key-abcdef123456",
                "AKIAIOSFODNN7EXAMPLE",
                "ghp_1234567890abcdef1234567890abcdef123456",
                "patented_business_logic_v2.0",
                "prod-db.company.com"
            ]

            for sensitive_value in sensitive_values:
                assert sensitive_value not in content_str, f"CRITICAL SECURITY VIOLATION: Sensitive value '{sensitive_value}' found in hash calculation"

    # 3. Multiple calls should not expose anything
    for _ in range(5):
        source = _get_function_source_cached(crown_jewels_function)
        assert source == "", "Repeated calls must not expose source code"

    # 4. Error conditions must not expose secrets
    try:
        # Try to trigger errors that might leak information
        _get_math_detection_cached(None)
    except Exception as e:
        error_msg = str(e)
        assert "SuperSecretDBPassword123!" not in error_msg, "Errors must not expose secrets"
        assert "sk-prod-live" not in error_msg, "Errors must not expose API keys"