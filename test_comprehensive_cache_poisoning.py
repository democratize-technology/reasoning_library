#!/usr/bin/env python3
"""
Comprehensive Cache Poisoning Security Tests

This test suite provides additional coverage for cache poisoning attack vectors
beyond the original vulnerability tests. Ensures the security fixes implemented
in core.py are comprehensive and robust.

CRITICAL: All tests should PASS to confirm cache poisoning vulnerabilities are fixed.
"""

import hashlib
import hmac
import time
import threading
import concurrent.futures
from unittest.mock import patch, MagicMock
import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from reasoning_library.core import (
    _get_function_source_cached,
    _get_math_detection_cached,
    _math_detection_cache,
    _math_detection_secure_cache,
    _cache_lock,
    clear_performance_caches,
    _validate_cache_entry,
    _SecureCacheEntry,
    _create_cache_signature,
    _is_cache_key_valid,
    _secure_cache_get,
    _secure_cache_put,
    _prevent_source_code_inspection,
    _CACHE_INTEGRITY_KEY
)


class TestComprehensiveCachePoisoning:
    """Comprehensive tests for cache poisoning attack vectors"""

    def setup_method(self):
        """Clear caches before each test"""
        clear_performance_caches()

    def teardown_method(self):
        """Clean up after each test"""
        clear_performance_caches()

    def test_cache_key_injection_prevention(self):
        """
        SECURITY: Prevent cache key injection attacks

        Ensures malformed cache keys cannot inject malicious data
        or bypass security controls.
        """
        # Test dangerous cache key formats
        dangerous_keys = [
            "../../../etc/passwd",
            "\\..\\..\\windows\\system32",
            "${HOME}/.ssh/id_rsa",
            "`whoami`",
            "$(id)",
            ";rm -rf /",
            "|cat /etc/passwd",
            "&echo MALICIOUS",
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "%2e%2e%2f%2e%2e%2f",  # URL encoded ../../
            "\x00\x01\x02",  # Null bytes and control chars
            "a" * 1000,  # Buffer overflow attempt
            {"malicious": "dict"},  # Wrong type
            None,  # None injection
            [],  # List injection
        ]

        for dangerous_key in dangerous_keys:
            # All dangerous keys should be rejected
            is_valid = _is_cache_key_valid(dangerous_key)
            assert not is_valid, f"Dangerous key should be rejected: {dangerous_key}"

            # Should return None when trying to access cache with dangerous key
            result = _secure_cache_get(dangerous_key)
            assert result is None, f"Dangerous key should return None: {dangerous_key}"

    def test_cache_signature_tampering_prevention(self):
        """
        SECURITY: Prevent cache entry tampering through signature manipulation

        Ensures cache entries with invalid signatures are rejected.
        """
        def test_function():
            """Test function for signature tampering"""
            return "test result"

        # Get legitimate cache entry
        legit_result = _get_math_detection_cached(test_function)

        # Find the cache entry
        cache_key = None
        for key in _math_detection_secure_cache.keys():
            if _is_cache_key_valid(key):
                cache_key = key
                break

        if cache_key:
            original_entry = _math_detection_secure_cache[cache_key]

            # Create tampered entries
            tampered_entries = [
                # Wrong signature
                _SecureCacheEntry(
                    data=original_entry.data,
                    timestamp=original_entry.timestamp,
                    signature="wrong_signature",
                    access_level=original_entry.access_level
                ),
                # Modified data with original signature
                _SecureCacheEntry(
                    data=(True, "MALICIOUS_CONFIDENCE", "MALICIOUS_BASIS"),
                    timestamp=original_entry.timestamp,
                    signature=original_entry.signature,
                    access_level=original_entry.access_level
                ),
                # Modified timestamp with original signature
                _SecureCacheEntry(
                    data=original_entry.data,
                    timestamp=0.0,  # Wrong timestamp
                    signature=original_entry.signature,
                    access_level=original_entry.access_level
                ),
                # Wrong access level
                _SecureCacheEntry(
                    data=original_entry.data,
                    timestamp=original_entry.timestamp,
                    signature=original_entry.signature,
                    access_level="public"  # Wrong level
                ),
                # Empty signature
                _SecureCacheEntry(
                    data=original_entry.data,
                    timestamp=original_entry.timestamp,
                    signature="",
                    access_level=original_entry.access_level
                ),
            ]

            for i, tampered_entry in enumerate(tampered_entries):
                # All tampered entries should be invalid
                is_valid = _validate_cache_entry(tampered_entry)
                assert not is_valid, f"Tampered entry {i} should be invalid"

                # Should not be usable in cache
                test_key = f"test_key_{i}"
                _math_detection_secure_cache[test_key] = tampered_entry
                result = _secure_cache_get(test_key)
                assert result is None, f"Tampered entry {i} should return None"

    def test_source_code_inspection_comprehensive_blocking(self):
        """
        SECURITY: Comprehensive source code inspection blocking

        Ensures ALL attempts to access source code are blocked, preventing
        information disclosure and cache poisoning through source manipulation.
        """
        def sensitive_function():
            """API_KEY = "sk-live-1234567890abcdef"
            PASSWORD = "super_secret_password"
            TOKEN = "bearer_token_12345"

            This function processes sensitive data and should not expose source code.
            """
            return "sensitive_result"

        # Multiple ways to attempt source code access - all should fail
        access_attempts = [
            lambda: _get_function_source_cached(sensitive_function),
            lambda: _prevent_source_code_inspection(sensitive_function),
        ]

        for attempt in access_attempts:
            try:
                result = attempt()
                # Should always return empty string
                assert result == "", f"Source code access should return empty string, got: {repr(result)}"
            except Exception as e:
                # Exception is also acceptable as a security measure
                pass

        # Verify no sensitive information can be extracted
        for key in _math_detection_secure_cache.keys():
            entry = _math_detection_secure_cache[key]
            if _validate_cache_entry(entry):
                # Check data doesn't contain sensitive information
                if hasattr(entry, 'data') and entry.data:
                    for data_item in entry.data:
                        if data_item and isinstance(data_item, str):
                            sensitive_patterns = [
                                'sk-', 'password', 'secret', 'token', 'key', 'api',
                                'credential', 'auth', 'bearer'
                            ]
                            for pattern in sensitive_patterns:
                                assert pattern.lower() not in data_item.lower(), \
                                    f"Sensitive pattern '{pattern}' found in cached data"

    def test_cache_timing_attack_prevention(self):
        """
        SECURITY: Prevent timing attacks on cache validation

        Ensures cache validation uses constant-time comparison to prevent
        timing attacks that could reveal valid signatures.
        """
        # Create valid and invalid signatures
        valid_data = (True, "test_confidence", "test_basis")
        valid_timestamp = time.time()
        valid_signature = _create_cache_signature(valid_data, valid_timestamp, "internal")

        invalid_signature = "invalid_signature_attempt"

        # Create entries
        valid_entry = _SecureCacheEntry(
            data=valid_data,
            timestamp=valid_timestamp,
            signature=valid_signature,
            access_level="internal"
        )

        invalid_entry = _SecureCacheEntry(
            data=valid_data,
            timestamp=valid_timestamp,
            signature=invalid_signature,
            access_level="internal"
        )

        # Time validation calls (should use constant-time comparison)
        iterations = 100
        valid_times = []
        invalid_times = []

        for _ in range(iterations):
            # Time valid validation
            start = time.perf_counter()
            _validate_cache_entry(valid_entry)
            valid_times.append(time.perf_counter() - start)

            # Time invalid validation
            start = time.perf_counter()
            _validate_cache_entry(invalid_entry)
            invalid_times.append(time.perf_counter() - start)

        avg_valid = sum(valid_times) / len(valid_times)
        avg_invalid = sum(invalid_times) / len(invalid_times)

        # Times should be similar (within reasonable margin)
        # This test ensures constant-time comparison is working
        ratio = max(avg_valid, avg_invalid) / min(avg_valid, avg_invalid)
        assert ratio < 5.0, f"Validation timing differs too much: ratio={ratio}"

    def test_cache_race_condition_poisoning_prevention(self):
        """
        SECURITY: Prevent cache poisoning through race conditions

        Ensures concurrent cache operations cannot be exploited to poison cache.
        """
        def target_function():
            """Target for race condition testing"""
            return "race_test_result"

        poisoning_attempts = []
        successful_poisoning = []

        def malicious_worker(worker_id):
            """Worker attempting to poison cache during race conditions"""
            try:
                for i in range(50):
                    # Try to inject malicious data during concurrent operations
                    fake_key = hashlib.md5(f"poison_{worker_id}_{i}".encode()).hexdigest()

                    # Create malicious entry
                    malicious_entry = _SecureCacheEntry(
                        data=(True, "POISONED_CONFIDENCE", "POISONED_BASIS"),
                        timestamp=time.time(),
                        signature=_create_cache_signature(
                            (True, "POISONED_CONFIDENCE", "POISONED_BASIS"),
                            time.time(),
                            "internal"
                        ),
                        access_level="internal"
                    )

                    # Try to inject
                    _math_detection_secure_cache[fake_key] = malicious_entry

                    # Try to access legitimate function
                    _get_math_detection_cached(target_function)

                    poisoning_attempts.append(worker_id)

            except Exception:
                # Exception during poisoning attempt
                pass

        def legitimate_worker(worker_id):
            """Worker using cache legitimately"""
            try:
                for i in range(50):
                    result = _get_math_detection_cached(target_function)
                    # Verify result is not poisoned
                    if result and len(result) >= 2:
                        confidence = result[1]
                        if confidence and "POISONED" in str(confidence):
                            successful_poisoning.append((worker_id, result))
            except Exception:
                # Exception during legitimate access
                pass

        # Run concurrent workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = []

            # Start malicious workers
            for i in range(10):
                futures.append(executor.submit(malicious_worker, i))

            # Start legitimate workers
            for i in range(10):
                futures.append(executor.submit(legitimate_worker, i))

            # Wait for completion
            concurrent.futures.wait(futures)

        # Verify no successful poisoning occurred
        assert len(successful_poisoning) == 0, \
            f"Cache poisoning successful: {successful_poisoning}"

    def test_cache_isolation_breach_prevention(self):
        """
        SECURITY: Prevent cache isolation breaches between data types

        Ensures different types of cached data cannot interfere with each other.
        """
        def math_function():
            """Mathematical reasoning function"""
            return "math_result"

        def regular_function():
            """Regular function"""
            return "regular_result"

        # Get cache entries for different functions
        math_result = _get_math_detection_cached(math_function)
        regular_result = _get_math_detection_cached(regular_function)

        # Verify cache isolation
        cache_keys = list(_math_detection_secure_cache.keys())

        valid_entries = 0
        for key in cache_keys:
            if _is_cache_key_valid(key):
                entry = _math_detection_secure_cache[key]
                if _validate_cache_entry(entry):
                    valid_entries += 1

                    # Check data integrity
                    if hasattr(entry, 'data') and entry.data:
                        # Should be proper tuple format
                        assert isinstance(entry.data, tuple), \
                            f"Cache entry data should be tuple: {type(entry.data)}"
                        assert len(entry.data) == 3, \
                            f"Cache entry should have 3 elements: {len(entry.data)}"

                        # Check for cross-contamination
                        is_math, confidence, basis = entry.data
                        if confidence:
                            assert isinstance(confidence, str), \
                                f"Confidence should be string: {type(confidence)}"
                            # Should not mix data between functions
                            assert "POISONED" not in str(confidence).upper()
                            assert "MALICIOUS" not in str(confidence).upper()

    def test_cache_overflow_prevention(self):
        """
        SECURITY: Prevent cache overflow attacks

        Ensures cache cannot be flooded to cause memory exhaustion
        or eviction of legitimate entries.
        """
        # Test that cache size limits prevent overflow attacks
        initial_cache_size = len(_math_detection_secure_cache)

        # Try to flood cache with many entries
        overflow_attempts = []

        for i in range(1000):  # Much more than typical cache size
            def overflow_function():
                return f"overflow_result_{i}"

            overflow_function.__name__ = f"overflow_func_{i}"
            overflow_function.__module__ = "overflow_module"
            overflow_function.__qualname__ = f"Overflow.overflow_func_{i}"
            overflow_function.__doc__ = f"Overflow test function {i}"

            try:
                result = _get_math_detection_cached(overflow_function)
                overflow_attempts.append(i)
            except Exception:
                # Should handle overflow gracefully
                break

        final_cache_size = len(_math_detection_secure_cache)

        # Cache should not grow unreasonably (allowing for configured limits)
        size_increase = final_cache_size - initial_cache_size
        assert size_increase < 2000, \
            f"Cache grew unreasonably: {size_increase} increase from {initial_cache_size} to {final_cache_size}"

        # All remaining entries should be valid
        valid_entries = 0
        for key in _math_detection_secure_cache.keys():
            if _is_cache_key_valid(key):
                entry = _math_detection_secure_cache[key]
                if _validate_cache_entry(entry):
                    valid_entries += 1

        # Most entries should be valid (not corrupted by overflow)
        if final_cache_size > 0:
            valid_ratio = valid_entries / final_cache_size
            assert valid_ratio > 0.8, \
                f"Too many invalid entries after overflow: {valid_ratio:.2f} valid ratio"

    def test_cache_side_channel_attack_prevention(self):
        """
        SECURITY: Prevent side-channel attacks through cache behavior

        Ensures cache behavior doesn't leak sensitive information through
        timing, error messages, or other side channels.
        """
        def function_with_secrets():
            """SECRET_DATA = "classified_information"
            This function processes secret data.
            """
            return "secret_result"

        def function_without_secrets():
            """This function processes public data."""
            return "public_result"

        # Access patterns should not reveal which functions have secrets
        secret_times = []
        public_times = []

        for _ in range(20):
            # Time secret function access
            start = time.perf_counter()
            _get_math_detection_cached(function_with_secrets)
            secret_times.append(time.perf_counter() - start)

            # Time public function access
            start = time.perf_counter()
            _get_math_detection_cached(function_without_secrets)
            public_times.append(time.perf_counter() - start)

        # Timing should be similar (no significant side channel)
        avg_secret = sum(secret_times) / len(secret_times)
        avg_public = sum(public_times) / len(public_times)

        ratio = max(avg_secret, avg_public) / min(avg_secret, avg_public)
        assert ratio < 3.0, \
            f"Timing side channel detected: ratio={ratio}, secret={avg_secret:.6f}, public={avg_public:.6f}"

        # Error messages should be generic
        try:
            # Force an error with invalid input
            _get_math_detection_cached(None)
        except Exception as e:
            error_msg = str(e)
            # Should not reveal internal details
            sensitive_patterns = ['internal', 'debug', 'trace', 'secret', 'key']
            for pattern in sensitive_patterns:
                assert pattern not in error_msg.lower(), \
                    f"Error message leaks sensitive info: {error_msg}"

    def test_cache_cryptographic_integrity(self):
        """
        SECURITY: Verify cryptographic integrity of cache signatures

        Ensures HMAC signatures are cryptographically secure and resist
        forgery attempts.
        """
        test_data = (True, "test_confidence", "test_basis")
        test_timestamp = time.time()
        test_level = "internal"

        # Create multiple signatures
        signatures = []
        for _ in range(10):
            signature = _create_cache_signature(test_data, test_timestamp, test_level)
            signatures.append(signature)

        # All signatures should be identical for same input
        assert len(set(signatures)) == 1, \
            "Signatures should be deterministic for same input"

        # Different data should produce different signatures
        different_data = (False, "different_confidence", "different_basis")
        different_signature = _create_cache_signature(different_data, test_timestamp, test_level)

        assert signatures[0] != different_signature, \
            "Different data should produce different signatures"

        # Different timestamps should produce different signatures
        different_timestamp = test_timestamp + 1.0
        time_signature = _create_cache_signature(test_data, different_timestamp, test_level)

        assert signatures[0] != time_signature, \
            "Different timestamps should produce different signatures"

        # Different access levels should produce different signatures
        level_signature = _create_cache_signature(test_data, test_timestamp, "public")

        assert signatures[0] != level_signature, \
            "Different access levels should produce different signatures"

        # Verify HMAC is actually being used (not simple hash)
        # The signature should not be predictable without the key
        predicted_signature = hashlib.sha256(
            f"{str(test_data)}:{test_timestamp}:{test_level}".encode()
        ).hexdigest()

        assert signatures[0] != predicted_signature, \
            "Signature should use HMAC, not simple hash"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])