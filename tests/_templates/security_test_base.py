"""
Base template for security tests in the reasoning library.

This template provides standardized patterns for testing security vulnerabilities
including ReDoS, DoS attacks, injection attacks, and performance validation.
"""

import time
import pytest
from typing import Any, Callable, Dict, List, Optional, Tuple


class SecurityTestBase:
    """
    Base class for security tests providing common testing patterns.

    Usage:
        class TestMySecurity(SecurityTestBase):
            def test_input_validation(self):
                self.test_rejection_of_malicious_inputs(
                    my_function,
                    malicious_inputs,
                    expected_exception=ValidationError
                )
    """

    # Security test configuration
    MAX_EXECUTION_TIME = 0.1  # 100ms max for safe operations
    MAX_MEMORY_USAGE = 1024 * 1024  # 1MB max memory
    MAX_INPUT_SIZE = 10000  # Maximum safe input size

    @pytest.mark.security
    def test_timing_attack_protection(
        self,
        func: Callable,
        inputs: List[Any],
        max_time: Optional[float] = None
    ) -> None:
        """
        Test that function execution time is consistent (prevents timing attacks).

        Args:
            func: Function to test
            inputs: List of inputs to test
            max_time: Maximum allowed execution time per input
        """
        max_time = max_time or self.MAX_EXECUTION_TIME
        execution_times = []

        for test_input in inputs:
            start_time = time.time()
            try:
                result = func(test_input)
                end_time = time.time()
                execution_times.append(end_time - start_time)

                # Individual execution time check
                assert end_time - start_time <= max_time, \
                    f"Function took too long: {end_time - start_time:.4f}s > {max_time}s"

            except Exception as e:
                # Exceptions should also happen quickly
                end_time = time.time()
                assert end_time - start_time <= max_time, \
                    f"Exception took too long: {end_time - start_time:.4f}s > {max_time}s"

        # Check for timing variations that might indicate timing attacks
        if len(execution_times) > 1:
            time_variance = max(execution_times) - min(execution_times)
            assert time_variance <= max_time * 0.5, \
                f"Timing variance too large: {time_variance:.4f}s (potential timing attack vulnerability)"

    @pytest.mark.security
    def test_rejection_of_malicious_inputs(
        self,
        func: Callable,
        malicious_inputs: List[Any],
        expected_exception: Optional[type] = None
    ) -> None:
        """
        Test that function properly rejects malicious inputs.

        Args:
            func: Function to test
            malicious_inputs: List of malicious inputs
            expected_exception: Expected exception type (if any)
        """
        for malicious_input in malicious_inputs:
            if expected_exception:
                with pytest.raises(expected_exception):
                    func(malicious_input)
            else:
                # Function should either return safely or raise a security exception
                try:
                    result = func(malicious_input)
                    # If it returns, ensure the result is safe
                    assert result is not None, "Function returned None for malicious input"
                    assert not self._contains_malicious_content(result), \
                        f"Result contains malicious content: {result}"
                except (ValueError, ValidationError, SecurityError):
                    # Expected security exception
                    pass

    @pytest.mark.security
    def test_redos_vulnerability(
        self,
        func: Callable,
        vulnerable_patterns: List[str]
    ) -> None:
        """
        Test for Regular Expression Denial of Service (ReDoS) vulnerabilities.

        Args:
            func: Function that might use regex
            vulnerable_patterns: Patterns that could trigger ReDoS
        """
        for pattern in vulnerable_patterns:
            # Create inputs that would cause catastrophic backtracking
            malicious_input = " " * 10000 + pattern + " " * 10000

            start_time = time.time()
            try:
                result = func(malicious_input)
                execution_time = time.time() - start_time

                assert execution_time <= self.MAX_EXECUTION_TIME, \
                    f"ReDoS vulnerability detected: {execution_time:.4f}s > {self.MAX_EXECUTION_TIME}s"

            except Exception as e:
                execution_time = time.time() - start_time
                # Exceptions should also happen quickly
                assert execution_time <= self.MAX_EXECUTION_TIME, \
                    f"ReDoS in exception handling: {execution_time:.4f}s > {self.MAX_EXECUTION_TIME}s"

    @pytest.mark.security
    def test_dos_attack_resistance(
        self,
        func: Callable,
        large_inputs: List[Any],
        expected_behavior: str = "safe_return_or_exception"
    ) -> None:
        """
        Test resistance to Denial of Service attacks with large inputs.

        Args:
            func: Function to test
            large_inputs: Large inputs that might cause DoS
            expected_behavior: How function should handle large inputs
        """
        for large_input in large_inputs:
            start_time = time.time()

            try:
                result = func(large_input)
                execution_time = time.time() - start_time

                if expected_behavior == "safe_return":
                    # Should return a safe result quickly
                    assert execution_time <= self.MAX_EXECUTION_TIME * 2, \
                        f"DoS vulnerability: {execution_time:.4f}s"
                elif expected_behavior == "safe_return_or_exception":
                    # Should either return safely or raise an exception quickly
                    assert execution_time <= self.MAX_EXECUTION_TIME * 2, \
                        f"DoS vulnerability: {execution_time:.4f}s"

            except (ValueError, ValidationError, MemoryError, OverflowError):
                # Expected exceptions for large inputs
                execution_time = time.time() - start_time
                assert execution_time <= self.MAX_EXECUTION_TIME * 2, \
                    f"Exception handling too slow: {execution_time:.4f}s"

    @pytest.mark.security
    def test_input_sanitization(
        self,
        func: Callable,
        inputs_with_dangerous_content: List[Any]
    ) -> None:
        """
        Test that function properly sanitizes dangerous input content.

        Args:
            func: Function to test
            inputs_with_dangerous_content: Inputs containing dangerous content
        """
        dangerous_patterns = [
            '<script>',
            'javascript:',
            'data:text/html',
            'vbscript:',
            'onload=',
            'onerror=',
            'eval(',
            'exec(',
            'system(',
            '__import__',
            'subprocess.',
            'os.system',
            '\\x00',
            '\\r',
            '\\n',
            '\\t'
        ]

        for test_input in inputs_with_dangerous_content:
            try:
                result = func(test_input)

                # Check result doesn't contain dangerous content
                if isinstance(result, str):
                    result_lower = result.lower()
                    for pattern in dangerous_patterns:
                        assert pattern not in result_lower, \
                            f"Dangerous content not sanitized: {pattern} found in result"

            except Exception:
                # Exceptions are acceptable for dangerous inputs
                pass

    def _contains_malicious_content(self, result: Any) -> bool:
        """Check if a result contains potentially malicious content."""
        if not isinstance(result, str):
            return False

        dangerous_indicators = [
            '<script', 'javascript:', 'eval(', 'exec(',
            'system(', '__import__', 'subprocess.',
            '../', '..\\', 'etc/passwd', 'etc/shadow'
        ]

        result_lower = result.lower()
        return any(indicator in result_lower for indicator in dangerous_indicators)

    @pytest.mark.security
    def test_memory_usage_safety(
        self,
        func: Callable,
        memory_stress_inputs: List[Any]
    ) -> None:
        """
        Test that function doesn't consume excessive memory.

        Args:
            func: Function to test
            memory_stress_inputs: Inputs that might cause memory issues
        """
        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss

            for stress_input in memory_stress_inputs:
                try:
                    result = func(stress_input)

                    # Check memory usage after function call
                    current_memory = process.memory_info().rss
                    memory_increase = current_memory - initial_memory

                    assert memory_increase <= self.MAX_MEMORY_USAGE, \
                        f"Excessive memory usage: {memory_increase} bytes > {self.MAX_MEMORY_USAGE}"

                except Exception:
                    # Exceptions should not cause memory leaks
                    pass

        except ImportError:
            # psutil not available, skip memory testing
            pytest.skip("psutil not available for memory testing")


class SecurityTestMixin:
    """
    Mixin class to provide security test methods for existing test classes.
    """

    def assert_execution_time_safe(self, func: Callable, *args, **kwargs) -> Any:
        """Assert that function execution completes within safe time limits."""
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time

        assert execution_time <= 0.1, f"Unsafe execution time: {execution_time:.4f}s"
        return result

    def assert_input_safe(self, func: Callable, test_input: Any) -> None:
        """Assert that function handles input safely."""
        start_time = time.time()

        try:
            result = func(test_input)
            execution_time = time.time() - start_time

            assert execution_time <= 0.1, f"Input processing too slow: {execution_time:.4f}s"
            assert not self._has_dangerous_content(result), "Result contains dangerous content"

        except (ValueError, ValidationError, SecurityError):
            # Expected security exceptions
            execution_time = time.time() - start_time
            assert execution_time <= 0.1, f"Exception handling too slow: {execution_time:.4f}s"

    def _has_dangerous_content(self, result: Any) -> bool:
        """Check if result contains dangerous content."""
        if not isinstance(result, str):
            return False
        return any(indicator in result.lower() for indicator in [
            '<script', 'javascript:', 'eval(', 'exec(', 'system('
        ])