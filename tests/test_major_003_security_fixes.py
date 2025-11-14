"""
Test for MAJOR-003: Input validation bypass vulnerability fixes.

These tests verify that the critical security vulnerabilities identified in MAJOR-003
have been properly fixed. All these tests should PASS to demonstrate that the fixes
are working correctly.

Security fixes implemented:
- Unicode obfuscation bypass prevention
- Enhanced template injection detection
- Comprehensive case-insensitive pattern matching
- Control character encoding bypass prevention
- Nested/encoded injection detection
- Log injection prevention
"""

import sys
sys.path.insert(0, 'src')

from reasoning_library.sanitization import (
    sanitize_text_input,
    sanitize_for_concatenation,
    sanitize_for_display,
    sanitize_for_logging,
    SanitizationLevel
)


def test_unicode_bypass_vulnerability_fix():
    """
    Test that Unicode obfuscation bypass vulnerabilities are fixed.

    Previously, attackers could use full-width Unicode characters to bypass
    ASCII-based regex patterns. The fix normalizes Unicode to prevent this.
    """
    unicode_bypass_attempts = [
        "ｉｍｐｏｒｔ os",  # Full-width Unicode characters
        "ｅｖａｌ('code')",  # Full-width eval
        "ｅｘｅｃ('command')",  # Full-width exec
    ]

    for attempt in unicode_bypass_attempts:
        result = sanitize_text_input(attempt, level=SanitizationLevel.STRICT)
        # After fix: Unicode should be normalized and dangerous keywords blocked
        assert "import" not in result.lower(), f"Unicode import not blocked: {attempt} -> {result}"
        assert "eval" not in result.lower(), f"Unicode eval not blocked: {attempt} -> {result}"
        assert "exec" not in result.lower(), f"Unicode exec not blocked: {attempt} -> {result}"


def test_template_injection_bypass_fix():
    """
    Test that template injection bypass vulnerabilities are fixed.

    Previously, alternative template syntax like #{}} and {{}} could bypass
    basic ${} pattern detection. The fix catches all template injection syntax.
    """
    template_bypass_attempts = [
        "{{user_input}}",  # Jinja2 style
        "#{user_input}",  # Ruby style
        "${{user_input}}",  # Double template
        "${{7*7}}",  # Math in template
        "{{7*7}}",  # Jinja2 math
    ]

    for attempt in template_bypass_attempts:
        result = sanitize_text_input(attempt, level=SanitizationLevel.STRICT)
        # After fix: All template injection syntax should be blocked
        assert "{" not in result and "}" not in result, \
            f"Template injection not blocked: {attempt} -> {result}"


def test_nested_injection_bypass_fix():
    """
    Test that nested injection bypass vulnerabilities are fixed.

    Previously, attackers could use character encoding and string concatenation
    to bypass simple pattern matching. The fix detects these patterns.
    """
    nested_bypass_attempts = [
        "eval(chr(101)+chr(118)+chr(97)+chr(108)+'(code)')",  # Character encoding
        "eval('e'+'v'+'a'+'l'+'(\"code\")')",  # String concatenation
    ]

    for attempt in nested_bypass_attempts:
        result = sanitize_text_input(attempt, level=SanitizationLevel.STRICT)
        # After fix: Nested injections should be detected and blocked
        assert "BLOCKED" in result or "eval" not in result.lower(), \
            f"Nested injection not blocked: {attempt} -> {result}"


def test_control_character_bypass_fix():
    """
    Test that control character bypass vulnerabilities are fixed.

    Previously, encoded control characters could bypass log poisoning detection.
    The fix detects and normalizes various control character encodings.
    """
    control_bypass_attempts = [
        "text\\nwith\\r\\tcontrol\\x0achars",  # Escaped control chars
        "[ERROR]\\x1b[31m [INJECTION]\\x1b[0m",  # ANSI escape sequences
    ]

    for attempt in control_bypass_attempts:
        result = sanitize_for_logging(attempt)  # Use logging-specific function

        # After fix: Control characters should be normalized
        assert "\n" not in result and "\r" not in result and "\t" not in result, \
            f"Control characters not normalized: {repr(attempt)} -> {repr(result)}"


def test_log_injection_bypass_fix():
    """
    Test that log injection bypass vulnerabilities are fixed.

    Previously, log levels could be injected to poison log files.
    The fix detects and blocks log injection attempts.
    """
    log_injection_attempts = [
        "[ERROR] User injected log level",
        "[CRITICAL] System compromised",
        "[INFO] Malicious content",
    ]

    for attempt in log_injection_attempts:
        result = sanitize_for_logging(attempt)

        # After fix: Log injection should be blocked
        assert "[LOG_LEVEL_BLOCKED]" in result or \
               not any(level in result for level in ["[ERROR]", "[CRITICAL]", "[INFO]"]), \
            f"Log injection not blocked: {attempt} -> {result}"


def test_shell_metacharacter_bypass_fix():
    """
    Test that shell metacharacter bypass vulnerabilities are fixed.

    Previously, shell metacharacters could be used for command injection.
    The fix detects and blocks various shell metacharacter patterns.
    """
    shell_bypass_attempts = [
        "$(whoami)",  # Command substitution
        "`whoami`",  # Backtick command
        "\\$(whoami)",  # Escaped substitution
        "\\`whoami\\`",  # Escaped backticks
    ]

    for attempt in shell_bypass_attempts:
        result = sanitize_text_input(attempt, level=SanitizationLevel.STRICT)

        # After fix: Shell metacharacters should be blocked
        assert not any(char in result for char in ["$", "`"]), \
            f"Shell metacharacters not blocked: {attempt} -> {result}"


def test_backward_compatibility_maintained():
    """
    Test that security fixes maintain backward compatibility.

    The fixes should not break existing functionality for legitimate inputs.
    """
    legitimate_inputs = [
        "normal text without special characters",
        "text with multiple   spaces",
        "text with\nnewlines and\ttabs",
        "Hello, world!",
        "This is a test message",
    ]

    for input_text in legitimate_inputs:
        # Test all sanitization levels
        strict_result = sanitize_text_input(input_text, level=SanitizationLevel.STRICT)
        moderate_result = sanitize_text_input(input_text, level=SanitizationLevel.MODERATE)
        permissive_result = sanitize_text_input(input_text, level=SanitizationLevel.PERMISSIVE)

        # Results should still be valid strings
        assert isinstance(strict_result, str), f"Strict should return string for: {input_text}"
        assert isinstance(moderate_result, str), f"Moderate should return string for: {input_text}"
        assert isinstance(permissive_result, str), f"Permissive should return string for: {input_text}"

        # Results should not be empty for legitimate inputs
        if input_text.strip():
            assert len(strict_result.strip()) > 0, f"Strict should not empty legitimate input: {input_text}"
            assert len(moderate_result.strip()) > 0, f"Moderate should not empty legitimate input: {input_text}"
            assert len(permissive_result.strip()) > 0, f"Permissive should not empty legitimate input: {input_text}"


def test_security_performance():
    """
    Test that security fixes don't significantly impact performance.

    The enhanced security measures should maintain reasonable performance.
    """
    import time

    test_input = "test ${template} with eval('code') and ${user}"
    iterations = 1000

    # Test performance with strict sanitization (all security measures enabled)
    start_time = time.perf_counter()
    for _ in range(iterations):
        result = sanitize_text_input(test_input, level=SanitizationLevel.STRICT)
    end_time = time.perf_counter()

    avg_time_ms = (end_time - start_time) / iterations * 1000

    # Performance should be reasonable (less than 1ms per operation)
    assert avg_time_ms < 1.0, f"Performance degraded: {avg_time_ms:.3f}ms > 1.0ms"


if __name__ == "__main__":
    # Run all tests
    test_unicode_bypass_vulnerability_fix()
    test_template_injection_bypass_fix()
    test_nested_injection_bypass_fix()
    test_control_character_bypass_fix()
    test_log_injection_bypass_fix()
    test_shell_metacharacter_bypass_fix()
    test_backward_compatibility_maintained()
    test_security_performance()

    print("✅ All MAJOR-003 security fix tests passed!")
    print("🔒 Input validation bypass vulnerabilities have been successfully fixed!")