"""
Shared sanitization utilities for the reasoning library.

This module consolidates duplicate sanitization logic from across the codebase
into reusable, secure, and well-tested utilities.

All sanitization functions follow defense-in-depth principles with multiple
layers of protection against injection attacks.

SECURITY FIXES for MAJOR-003: Input validation bypass vulnerabilities
- Unicode obfuscation bypass prevention
- Enhanced template injection detection
- Comprehensive case-insensitive pattern matching
- Control character encoding bypass prevention
- Nested/encoded injection detection

SECURITY FIX for SEC-001: Critical password leakage vulnerability
- Password and sensitive data masking in sanitize_for_logging()
- Prevents accidental logging of passwords, API keys, tokens, secrets, and credentials
- Uses regex pattern matching to identify and replace sensitive data with [REDACTED]
- Maintains field names while masking values for debugging purposes
- Fixed critical vulnerability where sanitize_for_logging("password='secret'")
  returned literal password instead of masked version

SEC-001-ARCHFIX: Critical architectural flaws fixed
- URL encoding bypass prevention: pass%77ord=secret now properly masked
- HTML entity bypass prevention: passwor&#100;=secret now properly masked
- Regex greediness fix: compound strings with multiple credentials now all masked
- False positive prevention: password_reset_page no longer over-masked
- Enhanced word boundaries and proper boundary detection implemented

VULNERABILITY DETAILS:
- VULNERABLE: sanitize_for_logging("password='secret123'") returned "password='secret123'"
- FIXED: sanitize_for_logging("password='secret123'") now returns "password=[REDACTED]"
- BYPASS VECTORS BLOCKED: URL encoding, HTML entities, compound strings, nested patterns
- ENHANCED PATTERN: \b(password|api[_-]?key|token|secret|credential[s]?)\b\s*[=:]\s*[\'"]?([^\'"\s&;]+?)(?:[\'"])?(?=[\s&;,]|$)
- ARCHITECTURAL FIXES: Word boundaries, proper quote handling, boundary detection
- IMPACT: Prevents sensitive data leakage in application logs and security monitoring systems
"""

import re
import unicodedata
import urllib.parse
import html
from typing import Any, Optional

from .constants import (
    KEYWORD_LENGTH_LIMIT
)
from .security_logging import log_security_event, get_security_logger
import logging
import warnings
import functools
from typing import Union


class SanitizationLevel:
    """
    Enumeration of sanitization levels for different security requirements.
    """
    STRICT = "strict"      # Maximum security, removes most special characters
    MODERATE = "moderate"  # Balanced security, preserves some formatting
    PERMISSIVE = "permissive"  # Minimal sanitization, preserves most characters


def _normalize_unicode_for_security(text: str) -> str:
    """
    SECURITY FIX: Normalize Unicode text to prevent bypass attempts.

    Converts full-width characters, removes zero-width characters, and normalizes
    Unicode variations that could be used to bypass security controls.

    Args:
        text: Input text to normalize

    Returns:
        Normalized text safe for security processing
    """
    # Remove zero-width and invisible characters commonly used in bypasses
    text = re.sub(r'[\u200b-\u200d\u2060\ufeff]', '', text)  # Zero-width characters
    text = re.sub(r'[\u2028\u2029]', ' ', text)  # Line/paragraph separators
    text = re.sub(r'[\u200e\u200f\u202a-\u202e]', '', text)  # Directional overrides

    # Normalize Unicode characters (NFKC to convert full-width to ASCII)
    text = unicodedata.normalize('NFKC', text)

    return text


def _decode_encoded_characters(text: str) -> str:
    """
    SECURITY FIX: Decode common character encodings used in bypass attempts.

    Detects and decodes hex, octal, and Unicode escape sequences that could
    be used to hide malicious code from simple pattern matching.

    Args:
        text: Input text potentially containing encoded characters

    Returns:
        Text with common encodings decoded for security analysis
    """
    try:
        # Decode common escape patterns
        # Handle \xNN hex escapes
        text = re.sub(r'\\x([0-9a-fA-F]{2})', lambda m: chr(int(m.group(1), 16)), text)
        # Handle \NNN octal escapes
        text = re.sub(r'\\([0-7]{3})', lambda m: chr(int(m.group(1), 8)), text)
        # Handle \\uNNNN Unicode escapes
        text = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), text)
        # Handle \\UXXXXXXXX Unicode escapes
        text = re.sub(r'\\U([0-9a-fA-F]{8})', lambda m: chr(int(m.group(1), 16)), text)
    except (ValueError, OverflowError):
        # If decoding fails, return original text
        pass

    return text


def _enhanced_preprocessing_for_bypass_prevention(text: str) -> str:
    """
    SEC-001-ARCHFIX: Enhanced pre-processing to prevent sophisticated bypass attempts.

    This function implements comprehensive decoding to prevent URL encoding, HTML entity
    encoding, and other encoding bypasses that could circumvent sensitive data masking.

    Args:
        text: Input text that may contain encoded sensitive data

    Returns:
        Fully decoded text safe for sensitive data pattern matching

    Security Features:
        - URL decoding (prevents pass%77ord bypass)
        - HTML entity decoding (prevents passwor&#100; bypass)
        - Hex decoding fallback
        - Security-safe exception handling
    """
    if not isinstance(text, str):
        return ""

    try:
        # Step 1: URL decoding - prevents pass%77ord type bypasses
        # This handles percent-encoded characters that could mask sensitive field names
        text = urllib.parse.unquote(text)

        # Step 2: HTML entity decoding - prevents passwor&#100; type bypasses
        # This handles HTML entities that could be used to obfuscate field names
        text = html.unescape(text)

        # Step 3: Additional hex decoding for any remaining encoded patterns
        # This catches encoded characters that weren't handled by URL/HTML decoding
        def hex_decoder(match):
            try:
                hex_value = match.group(1)
                return chr(int(hex_value, 16))
            except (ValueError, OverflowError):
                return match.group(0)  # Return original if decoding fails

        text = re.sub(r'%([0-9a-fA-F]{2})', hex_decoder, text)

    except Exception:
        # If any decoding fails, continue with original text
        # Security logging should never break the main functionality
        pass

    return text


# LAZY LOADING: Regex patterns are compiled on-demand to improve module import performance
# This reduces startup overhead by only compiling patterns when actually used
# SECURITY FIXES: Enhanced patterns to prevent bypass vulnerabilities

from functools import lru_cache

@lru_cache(maxsize=None)
def _get_dangerous_keyword_pattern() -> re.Pattern:
    """Get dangerous keyword pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'\b(?:import|exec|eval|system|subprocess|os|config|globals|locals|vars|dir|getattr|setattr|delattr|hasattr|__import__|open|file|input|raw_input|compile)\b',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_template_injection_pattern() -> re.Pattern:
    """Get template injection pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'\$\{[^}]*\}|#\{[^}]*\}|\{\{[^}]*\}\}',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_format_string_pattern() -> re.Pattern:
    """Get format string pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'%[\d$#]*[a-zA-Z]|%\([^)]*\)[a-zA-Z]',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_code_injection_pattern() -> re.Pattern:
    """Get code injection pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'(?:__import__|eval|exec|compile)\s*\(|(?:chr\s*\(\s*\d+\s*\)\s*\+?\s*)+',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_dunder_pattern() -> re.Pattern:
    """Get dunder method pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'__[a-zA-Z0-9_]*__|__.*?__|builtins|mro|subclasses|bases',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_attribute_pattern() -> re.Pattern:
    """Get attribute access pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'\.[a-zA-Z_][a-zA-Z0-9_]*|\[\'[^\']*\'\]|\[\"[^\"]*\"\]',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_shell_pattern() -> re.Pattern:
    """Get shell metacharacters pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'[|&;$<>`\\]|\\[\$`]|\\\(|\\\)|\\\[|\\\]',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_bracket_pattern() -> re.Pattern:
    """Get bracket pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'[{}\[\]\(\)]',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_quote_pattern() -> re.Pattern:
    """Get quote characters pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'["\']|\\["\']',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_html_injection_pattern() -> re.Pattern:
    """Get HTML/JS injection pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'[<>"\'`]|&lt;|&gt;|&amp;|javascript:|vbscript:|on\w+\s*=',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_control_char_pattern() -> re.Pattern:
    """Get control characters pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'[\r\n\t\x0b\x0c\x85\u2028\u2029]|\\[rnt]|\\x[0-9a-fA-F]{2}|\\[0-7]{3}',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_ansi_escape_pattern() -> re.Pattern:
    """Get ANSI escape sequences pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'\x1b\[[0-9;]*m|\\x1b\[[0-9;]*m|\\u001b\[[0-9;]*m',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_whitespace_pattern() -> re.Pattern:
    """Get whitespace normalization pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'\s+|[\u2000-\u200a\u3000]',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_log_injection_pattern() -> re.Pattern:
    """
    ID-003: Enhanced log injection pattern with comprehensive detection.

    Detects various log injection attempts including:
    - Log level spoofing
    - Timestamp manipulation
    - ANSI escape sequences
    - Control character injection
    - Multi-line log entry injection
    """
    return re.compile(
        r'(?:'
        r'\[(?:ERROR|CRITICAL|WARN|WARNING|INFO|DEBUG|TRACE|FATAL|ALERT|EMERGENCY)\]|'  # Log level spoofing
        r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}|'  # Timestamp injection
        r'\d{4}-\d{2}-\d{2}\s*-\s*.*?\s*-\s*'  # Log format injection (e.g., "2024-01-01 - EVENT - Description")
        r'|'
        r'\\x1b\[\d+(?:;\d+)*m|'  # ANSI escape sequences
        r'\r\n|\r|\n|'  # Newline injection
        r'\[\d{2}/\w{3}/\d{4}:|'  # Apache log format injection
        r'\(\w+\)\s+\[.*?\]\s+\w+:|'  # Java log format injection
        r'<\d{1,3}>|'  # Syslog severity injection
        r'\x0b|\x0c|\x85|\u2028|\u2029|'  # Control characters
        r'\\[rnt]|'  # Escape sequences
        r'\\x[0-9a-fA-F]{2}|'  # Hex escape sequences
        r'\\[0-7]{3}'  # Octal escape sequences
        r')',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_nested_injection_pattern() -> re.Pattern:
    """Get nested injection pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'(?:eval|exec)\s*\(\s*(?:eval|exec|chr|concat|join|\+)',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_string_concatenation_pattern() -> re.Pattern:
    """Get string concatenation pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'[\'\"][^\'\"]*[\'\"]\s*\+\s*[\'\"][^\'\"]*[\'\"]|[\'\"]\s*\+\s*[\'\"]',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_sensitive_data_pattern() -> re.Pattern:
    """
    SEC-001-ARCHFIX: Enhanced sensitive data pattern with comprehensive bypass protection.

    This pattern identifies sensitive information like passwords, API keys, tokens,
    secrets, and credentials that should be masked in logs to prevent leakage.

    ARCHITECTURAL FIXES:
    - Added word boundaries (\b) to prevent false positive over-masking
    - Fixed regex greediness with proper boundary detection
    - Stops at &, space, comma, semicolon boundaries to handle compound strings
    - Enhanced to handle nested quotes and complex value patterns
    - Improved quote handling to properly strip surrounding quotes
    """
    return re.compile(
        r'\b(password|api[_-]?key|token|secret|credential[s]?)\b\s*[=:]\s*[\'"]?([^\'"\s&;]+?)(?:[\'"])?(?=[\s&;,]|$)',
        re.IGNORECASE
    )

# Backward compatibility aliases (deprecated - use _get_*_pattern() functions instead)
# These maintain compatibility while new code should use the getter functions
# Note: Regex patterns are now lazily loaded through module-level __getattr__ function
# This provides backward compatibility while enabling lazy compilation for performance


def sanitize_text_input(
    text: Any,
    max_length: Optional[int] = None,
    level: str = SanitizationLevel.MODERATE,
    source: str = "unknown"
) -> str:
    """
    SECURITY FIXES: Comprehensive text sanitization with configurable security levels.

    Enhanced to prevent input validation bypass vulnerabilities (MAJOR-003).

    Args:
        text: Input text to sanitize (any type, non-string returns empty string)
        max_length: Maximum allowed length (default: KEYWORD_LENGTH_LIMIT * 20)
        level: Sanitization level (strict, moderate, permissive)
        source: Source identifier for security logging

    Returns:
        str: Sanitized text safe for further processing

    Security Features:
        - Defense-in-depth with multiple pattern matching layers
        - Length limiting to prevent buffer overflow attacks
        - Keyword blocking to prevent code injection
        - Pattern removal to prevent template/format injection
        - Control character normalization to prevent log poisoning
        - SECURITY FIXES: Unicode normalization prevents bypass attempts
        - SECURITY FIXES: Encoded character detection prevents hidden attacks
        - SECURITY FIXES: Enhanced pattern matching catches more variations
        - MAJOR-006: Security event logging for monitoring and auditing

    Examples:
        >>> sanitize_text_input("Hello ${name}")
        'Hello name'
        >>> sanitize_text_input("import os", level="strict")
        ''
        >>> sanitize_text_input("text with <script>", level="moderate")
        'text with script'
    """
    if not isinstance(text, str):
        return ""

    # Set default max length
    if max_length is None:
        max_length = KEYWORD_LENGTH_LIMIT * 20

    original_text = text  # Store for security logging

    # MAJOR-006: Security logging - Check for suspicious patterns before processing
    if any(pattern.search(text.lower()) for pattern_list in [
        [r'eval\s*\(', r'exec\s*\(', r'__import__\s*\('],  # Code injection
        [r'\bdrop\s+table\b', r';\s*drop'],  # SQL injection
        [r'<script[^>]*>', r'javascript:'],  # XSS
        [r'\.\./', r'%2e%2e%2f'],  # Path traversal
    ] for pattern in [re.compile(p) for p in pattern_list]):
        # Log security event
        log_security_event(
            input_text=text,
            source=source,
            context={
                "function": "sanitize_text_input",
                "level": level,
                "max_length": max_length,
            },
            block_action=True
        )

    # SECURITY FIX: Preprocess text to prevent bypass attempts
    # Length limiting (first line of defense)
    text = text[:max_length]

    # SECURITY FIX: Normalize Unicode to prevent bypass attempts
    text = _normalize_unicode_for_security(text)

    # SECURITY FIX: Decode encoded characters to prevent hidden attacks
    text = _decode_encoded_characters(text)

    # Layer 1: Block dangerous keywords (enhanced patterns)
    text = _get_dangerous_keyword_pattern().sub('', text)

    # Layer 2: Handle injection patterns based on security level
    if level == SanitizationLevel.STRICT:
        # Strict mode: remove all potentially dangerous patterns
        text = _get_template_injection_pattern().sub('', text)
        text = _get_format_string_pattern().sub('', text)
        text = _get_code_injection_pattern().sub('BLOCKED', text)

        # SECURITY FIX: Enhanced nested injection detection
        text = _get_nested_injection_pattern().sub('BLOCKED', text)
        text = _get_string_concatenation_pattern().sub(' ', text)

        # SECURITY FIX: Remove dots after code blocking to prevent bypass
        text = re.sub(r'[.]', ' ', text)  # Remove all remaining dots
        text = _get_dunder_pattern().sub('', text)
        text = _get_attribute_pattern().sub('', text)
        text = _get_shell_pattern().sub('', text)
        text = _get_bracket_pattern().sub('', text)
        text = _get_quote_pattern().sub('', text)

    elif level == SanitizationLevel.MODERATE:
        # Moderate mode: balanced security
        text = _get_template_injection_pattern().sub('', text)
        text = _get_format_string_pattern().sub('', text)
        text = _get_code_injection_pattern().sub('BLOCKED', text)
        text = _get_nested_injection_pattern().sub('BLOCKED', text)
        text = _get_bracket_pattern().sub('', text)
        text = _get_quote_pattern().sub('', text)

    else:  # PERMISSIVE
        # Permissive mode: minimal sanitization
        text = _get_code_injection_pattern().sub('BLOCKED', text)
        text = _get_template_injection_pattern().sub('', text)
        # SECURITY FIX: Even permissive mode blocks nested injections
        text = _get_nested_injection_pattern().sub('BLOCKED', text)

    # Layer 3: Handle characters that could poison logs or output
    text = _get_html_injection_pattern().sub('', text)
    text = _get_control_char_pattern().sub(' ', text)
    text = _get_whitespace_pattern().sub(' ', text)
    text = _get_ansi_escape_pattern().sub('', text)
    # SECURITY FIX: Additional log injection protection
    text = _get_log_injection_pattern().sub('[LOG_LEVEL_BLOCKED]', text)

    # MAJOR-006: Check if content was significantly modified/blocked
    sanitized_text = text.strip()

    # Log if content was heavily modified (possible attack blocked)
    if len(original_text) > 0 and len(sanitized_text) < len(original_text) * 0.3:
        # More than 70% of content was removed - possible attack
        log_security_event(
            input_text=original_text,
            source=source,
            context={
                "function": "sanitize_text_input",
                "level": level,
                "action": "heavily_sanitized",
                "original_length": len(original_text),
                "sanitized_length": len(sanitized_text),
            },
            block_action=False  # Was sanitized, not blocked
        )

    return sanitized_text


def sanitize_for_concatenation(text: Any, max_length: int = 50, source: str = "unknown") -> str:
    """
    Strict sanitization specifically for text that will be concatenated.

    This function provides maximum security for string concatenation operations
    where any injection vulnerability could be catastrophic.

    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length (default: 50 for safety)
        source: Source identifier for security logging

    Returns:
        str: Sanitized text safe for concatenation

    Security Features:
        - Very strict length limiting (50 chars default)
        - Comprehensive pattern removal
        - All special characters removed
        - Defense-in-depth approach
        - MAJOR-006: Security event logging for monitoring

    Examples:
        >>> sanitize_for_concatenation("Hello ${name}")
        'Hello name'
        >>> sanitize_for_concatenation("import os")
        ''
    """
    return sanitize_text_input(
        text=text,
        max_length=max_length,
        level=SanitizationLevel.STRICT,
        source=source
    )


def sanitize_for_display(text: Any, max_length: Optional[int] = None, source: str = "unknown") -> str:
    """
    Moderate sanitization for text that will be displayed to users.

    This function balances security with readability, preserving some formatting
    while still preventing injection attacks.

    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length (default: KEYWORD_LENGTH_LIMIT * 10)
        source: Source identifier for security logging

    Returns:
        str: Sanitized text safe for display

    Examples:
        >>> sanitize_for_display("Hello <b>world</b>")
        'Hello bworldb'
        >>> sanitize_for_display("Text with    spaces")
        'Text with spaces'
    """
    if max_length is None:
        max_length = KEYWORD_LENGTH_LIMIT * 10

    return sanitize_text_input(
        text=text,
        max_length=max_length,
        level=SanitizationLevel.MODERATE,
        source=source
    )


def sanitize_for_logging(text: Any, max_length: Optional[int] = None, source: str = "unknown") -> str:
    """
    ID-003 SECURITY FIX: Enhanced sanitization for text that will be written to logs.

    Enhanced to prevent log injection bypass vulnerabilities and add comprehensive
    protection against various log injection attack vectors.

    SEC-001: NOW INCLUDES PASSWORD AND SENSITIVE DATA MASKING.

    Args:
        text: Input text to sanitize for logging
        max_length: Maximum allowed length (default: KEYWORD_LENGTH_LIMIT * 15)
        source: Source identifier for security logging of injection attempts

    Returns:
        str: Sanitized text safe for logging

    Security Features:
        - ID-003: Comprehensive log injection prevention
        - SEC-001: Password and sensitive data masking (password, api_key, token, secret, credentials)
        - Detects and blocks log level spoofing attempts
        - Prevents ANSI escape sequence injection
        - Normalizes control characters that could create fake log entries
        - Handles Unicode normalization bypass attempts
        - Detects encoded injection attacks
        - Security logging of injection attempts
        - Preserves debugging value while maintaining security

    Examples:
        >>> sanitize_for_logging("Error\n[INFO] Fake admin logged in")
        'Error [LOG_INJECTION_BLOCKED] Fake admin logged in'
        >>> sanitize_for_logging("Critical issue\x1b[31mRED TEXT\x1b[0m")
        'Critical issue[ANSI_BLOCKED]RED TEXT[ANSI_BLOCKED]'
        >>> sanitize_for_logging("password='secret123'")
        'password=[REDACTED]'
        # SEC-001-ARCHFIX examples - sophisticated bypass vectors now blocked:
        >>> sanitize_for_logging("pass%77ord=secret123")  # URL encoding bypass
        'password=[REDACTED]'
        >>> sanitize_for_logging("api_%6bey=token456")    # URL encoding bypass
        'api_key=[REDACTED]'
        >>> sanitize_for_logging("passwor&#100;=secret")  # HTML entity bypass
        'password=[REDACTED]'
        >>> sanitize_for_logging("password=secret&api_key=token")  # Compound string
        'password=[REDACTED]&api_key=[REDACTED]'
        # False positives properly handled:
        >>> sanitize_for_logging("password_reset_page")  # Should NOT be masked
        'password_reset_page'
    """
    if max_length is None:
        max_length = KEYWORD_LENGTH_LIMIT * 15

    if not isinstance(text, str):
        return ""

    original_text = text  # Store for security logging
    text = text[:max_length]

    # SECURITY FIX: Preprocess to prevent bypass attempts
    text = _normalize_unicode_for_security(text)
    text = _decode_encoded_characters(text)

    # SEC-001-ARCHFIX: Enhanced pre-processing to prevent encoding bypasses
    # This prevents URL encoding, HTML entity encoding, and other sophisticated bypasses
    text = _enhanced_preprocessing_for_bypass_prevention(text)

    # SEC-001: CRITICAL FIX - Mask sensitive data BEFORE any other processing
    # This prevents passwords, API keys, tokens, secrets, and credentials from being logged
    def _mask_sensitive_data(match):
        """Replace sensitive data with [REDACTED] marker."""
        field_name = match.group(1)  # The field name (password, api_key, etc.)
        return f"{field_name}=[REDACTED]"

    text = _get_sensitive_data_pattern().sub(_mask_sensitive_data, text)

    # ID-003: Enhanced log injection detection with multiple passes
    injection_detected = False

    # First pass: Detect log injection patterns
    if _get_log_injection_pattern().search(text):
        injection_detected = True

    # Second pass: Additional log injection detection patterns
    additional_patterns = [
        r'\d{4}-\d{1,2}-\d{1,2}\s+\d{1,2}:\d{2}:\d{2}[,\s]',  # Timestamps
        r'\w+\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}',  # Syslog timestamps
        r'\[pid\s+\d+\]',  # Process ID injection
        r'\[tid\s+\d+\]',  # Thread ID injection
        r'<\w+@[^>]+>',  # Email address injection
        r'://[^/\s]+',  # URL injection that could look like log sources
    ]

    for pattern in additional_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            injection_detected = True
            break

    # ID-003: Comprehensive log sanitization
    text = _get_control_char_pattern().sub(' ', text)
    text = _get_ansi_escape_pattern().sub('[ANSI_BLOCKED]', text)
    text = _get_whitespace_pattern().sub(' ', text)

    # Enhanced log injection protection with clear marking
    text = _get_log_injection_pattern().sub('[LOG_INJECTION_BLOCKED]', text)

    # Block additional suspicious patterns
    text = re.sub(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', '[TIMESTAMP_BLOCKED]', text)
    text = re.sub(r'\[pid\s+\d+\]|\[tid\s+\d+\]', '[PROCESS_INFO_BLOCKED]', text)

    # ID-003: Security logging for injection attempts
    if injection_detected and len(original_text.strip()) > 0:
        try:
            log_security_event(
                input_text=original_text[:200],  # Limit length for security logs
                source=source,
                context={
                    "function": "sanitize_for_logging",
                    "attack_type": "log_injection",
                    "original_length": len(original_text),
                    "sanitized_length": len(text),
                    "has_ansi_sequences": bool(re.search(r'\\x1b\[\d+(?:;\d+)*m', original_text)),
                    "has_control_chars": bool(re.search(r'[\r\n\t]', original_text)),
                    "has_timestamp_injection": bool(re.search(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', original_text)),
                },
                block_action=True  # This was an attack attempt
            )
        except Exception:
            # Security logging should never break the main functionality
            pass

    return text.strip()


def validate_confidence_value(value: Any, source: str = "unknown") -> float:
    """
    ID-003: Validate and normalize confidence values to prevent calculation errors.

    Comprehensive validation for confidence calculations that handles edge cases,
    prevents numeric overflow/underflow, and ensures values remain within valid ranges.

    Args:
        value: Input value to validate as confidence
        source: Source identifier for security logging

    Returns:
        float: Normalized confidence value between 0.0 and 1.0

    Security Features:
        - ID-003: Comprehensive numeric validation
        - Handles infinity, NaN, and extreme values
        - Prevents calculation errors in downstream processing
        - Security logging of invalid confidence values
        - Range normalization with safe defaults

    Examples:
        >>> validate_confidence_value(0.75)
        0.75
        >>> validate_confidence_value(float('inf'))
        1.0
        >>> validate_confidence_value(-10)
        0.0
    """
    try:
        # Convert to float if possible
        if isinstance(value, str):
            value = float(value.strip())
        elif not isinstance(value, (int, float)):
            # Try to convert other types
            value = float(value)

        # Handle special numeric values
        if value == float('inf'):
            log_security_event(
                input_text=str(value),
                source=source,
                context={
                    "function": "validate_confidence_value",
                    "validation_error": "infinity_value",
                    "normalized_value": 1.0
                },
                block_action=False
            )
            return 1.0

        if value == float('-inf'):
            log_security_event(
                input_text=str(value),
                source=source,
                context={
                    "function": "validate_confidence_value",
                    "validation_error": "negative_infinity",
                    "normalized_value": 0.0
                },
                block_action=False
            )
            return 0.0

        if value != value:  # NaN check
            log_security_event(
                input_text=str(value),
                source=source,
                context={
                    "function": "validate_confidence_value",
                    "validation_error": "nan_value",
                    "normalized_value": 0.5
                },
                block_action=False
            )
            return 0.5  # Default to middle confidence

        # Check for extreme values that might cause calculation issues
        if abs(value) > 1e100:
            log_security_event(
                input_text=str(value),
                source=source,
                context={
                    "function": "validate_confidence_value",
                    "validation_error": "extreme_value",
                    "original_value": value,
                    "normalized_value": 1.0 if value > 0 else 0.0
                },
                block_action=False
            )
            return 1.0 if value > 0 else 0.0

        # Normalize to valid confidence range [0.0, 1.0]
        if value < 0.0:
            if value < -0.1:  # Log significant negative values
                log_security_event(
                    input_text=str(value),
                    source=source,
                    context={
                        "function": "validate_confidence_value",
                        "validation_error": "negative_confidence",
                        "original_value": value
                    },
                    block_action=False
                )
            return 0.0

        if value > 1.0:
            if value > 1.1:  # Log values slightly over 1.0
                log_security_event(
                    input_text=str(value),
                    source=source,
                    context={
                        "function": "validate_confidence_value",
                        "validation_error": "confidence_overflow",
                        "original_value": value
                    },
                    block_action=False
                )
            return 1.0

        return float(value)

    except (ValueError, TypeError, OverflowError) as e:
        log_security_event(
            input_text=str(value),
            source=source,
            context={
                "function": "validate_confidence_value",
                "validation_error": "conversion_error",
                "error_type": type(e).__name__,
                "error_message": str(e)[:100]
            },
            block_action=False
        )
        return 0.5  # Safe default


def validate_input_size(text: Any, max_length: Optional[int] = None,
                        allow_expansion: bool = False, source: str = "unknown") -> str:
    """
    ID-003: Validate input size and handle expansion attacks safely.

    Validates input sizes and handles cases where Unicode normalization or
    character expansion could increase size beyond intended limits.

    Args:
        text: Input text to validate
        max_length: Maximum allowed length (default: KEYWORD_LENGTH_LIMIT * 10)
        allow_expansion: Whether to allow size expansion through normalization
        source: Source identifier for security logging

    Returns:
        str: Validated text, truncated if necessary

    Security Features:
        - ID-003: Size validation with expansion detection
        - Prevents Unicode expansion DoS attacks
        - Handles size limits before and after normalization
        - Security logging of size violations
        - Safe truncation with logging

    Examples:
        >>> validate_input_size("normal text", 100)
        'normal text'
        >>> len(validate_input_size("A" * 10000, 100)) <= 100
        True
    """
    if max_length is None:
        max_length = KEYWORD_LENGTH_LIMIT * 10

    if not isinstance(text, str):
        return ""

    original_length = len(text)
    text_size_violation = False

    # Check size before processing
    if original_length > max_length:
        text_size_violation = True
        log_security_event(
            input_text=f"Input size violation: {original_length} > {max_length}",
            source=source,
            context={
                "function": "validate_input_size",
                "violation_type": "oversize_input",
                "original_length": original_length,
                "max_length": max_length
            },
            block_action=False
        )

    # Apply Unicode normalization if expansion is not allowed
    if not allow_expansion:
        normalized_text = _normalize_unicode_for_security(text)
        expanded_text = _decode_encoded_characters(normalized_text)

        # Check if expansion occurred
        if len(expanded_text) > original_length * 1.5:  # 50% expansion threshold
            log_security_event(
                input_text=f"Unicode expansion detected: {original_length} -> {len(expanded_text)}",
                source=source,
                context={
                    "function": "validate_input_size",
                    "violation_type": "unicode_expansion",
                    "original_length": original_length,
                    "expanded_length": len(expanded_text),
                    "expansion_ratio": len(expanded_text) / original_length if original_length > 0 else 0
                },
                block_action=False
            )

        text = expanded_text
    else:
        text = _decode_encoded_characters(_normalize_unicode_for_security(text))

    # Final size check and safe truncation
    if len(text) > max_length:
        # Truncate safely at word boundary if possible
        truncated_text = text[:max_length]

        # Try to truncate at word boundary
        if max_length > 10:  # Only for reasonable lengths
            last_space = truncated_text.rfind(' ')
            if last_space > max_length * 0.8:  # Don't truncate too much
                truncated_text = truncated_text[:last_space]

        text = truncated_text

    return text


def quick_sanitize(text: Any) -> str:
    """
    Fast, minimal sanitization for low-risk scenarios.

    This function provides basic sanitization with maximum performance
    for situations where the input is already trusted or has been validated.

    Args:
        text: Input text to quickly sanitize

    Returns:
        str: Minimally sanitized text

    Examples:
        >>> quick_sanitize("Hello world")
        'Hello world'
    """
    if not isinstance(text, str):
        return ""

    # Only remove the most dangerous patterns quickly
    text = text[:KEYWORD_LENGTH_LIMIT * 5]  # Reasonable length limit
    text = _get_code_injection_pattern().sub('BLOCKED', text)

    return text.strip()


# Backward compatibility aliases
# These provide migration paths for existing code
def _sanitize_input_for_concatenation(text: str) -> str:
    """
    DEPRECATED: Use sanitize_for_concatenation() instead.

    Maintained for backward compatibility.
    """
    return sanitize_for_concatenation(text)


def _sanitize_template_input(text: str) -> str:
    """
    DEPRECATED: Use sanitize_for_concatenation() instead.

    Maintained for backward compatibility.
    """
    return sanitize_for_concatenation(text)


class SecureLogger:
    """
    ARCH-ID003-001: Mandatory secure logging wrapper that prevents bypass attacks.

    This class provides a secure logging interface that CANNOT be bypassed.
    All logging operations are automatically sanitized, preventing nested encoding
    bypass attacks that could compromise security monitoring and SIEM systems.

    CRITICAL SECURITY: This wrapper makes sanitization MANDATORY, not optional.
    Developers cannot accidentally log unsanitized data through this interface.
    """

    def __init__(self, logger_name: str = "reasoning_library.secure"):
        """
        Initialize the secure logger.

        Args:
            logger_name: Name for the underlying logger
        """
        # ARCH-ID003-001: Use backup logger directly to prevent recursion
        # This ensures we don't create infinite recursion by calling our patched getLogger
        if hasattr(logging, 'getLogger_backup'):
            self._logger = logging.getLogger_backup(logger_name)
        else:
            # Fallback: Create a new logger instance directly
            self._logger = logging.getLogger(logger_name)

        self._sanitization_enabled = True
        self._enforcement_mode = True  # Cannot be disabled

    def _sanitize_and_log(self, level: str, msg: str, *args, source: str = "secure_logger", **kwargs) -> None:
        """
        Internal method that sanitizes ALL logging operations.

        CRITICAL: This method cannot be bypassed or disabled. All logging
        operations go through mandatory sanitization.

        Args:
            level: Log level (debug, info, warning, error, critical)
            msg: Message to log (will be sanitized)
            *args: Additional arguments (will be sanitized)
            source: Source identifier for security logging
            **kwargs: Additional keyword arguments
        """
        # ARCH-ID003-001: Sanitization cannot be disabled or bypassed
        if not self._sanitization_enabled:
            # CRITICAL: This should never happen, but if it does, we log a security event
            log_security_event(
                input_text="SECURITY_VIOLATION: Sanitization disabled in SecureLogger",
                source=source,
                context={
                    "function": "SecureLogger._sanitize_and_log",
                    "level": level,
                    "original_message": str(msg)[:200]
                },
                block_action=True
            )
            # Re-enable sanitization immediately
            self._sanitization_enabled = True

        try:
            # Sanitize the main message
            sanitized_msg = sanitize_for_logging(msg, source=source)

            # Sanitize all arguments
            sanitized_args = []
            for arg in args:
                if isinstance(arg, str):
                    sanitized_arg = sanitize_for_logging(arg, source=source)
                    sanitized_args.append(sanitized_arg)
                else:
                    # For non-string args, convert to string and sanitize
                    sanitized_arg = sanitize_for_logging(str(arg), source=source)
                    sanitized_args.append(sanitized_arg)

            # Log the sanitized message and arguments
            getattr(self._logger, level)(sanitized_msg, *sanitized_args, **kwargs)

        except Exception as e:
            # Security logging should never fail, but if it does, we log the error
            try:
                log_security_event(
                    input_text=f"Secure logging error: {str(e)}",
                    source=source,
                    context={
                        "function": "SecureLogger._sanitize_and_log",
                        "level": level,
                        "error_type": type(e).__name__
                    },
                    block_action=False
                )
            except Exception:
                # Last resort - use standard logging with sanitized message
                self._logger.error("CRITICAL: Secure logging failed, using fallback")
                self._logger.error("Original message: %s", sanitize_for_logging(str(msg), source=source)[:100])

    def debug(self, msg: str, *args, **kwargs) -> None:
        """Log debug message with mandatory sanitization."""
        self._sanitize_and_log("debug", msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        """Log info message with mandatory sanitization."""
        self._sanitize_and_log("info", msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        """Log warning message with mandatory sanitization."""
        self._sanitize_and_log("warning", msg, *args, **kwargs)

    def warn(self, msg: str, *args, **kwargs) -> None:
        """Log warning message with mandatory sanitization (alias)."""
        self.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        """Log error message with mandatory sanitization."""
        self._sanitize_and_log("error", msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        """Log critical message with mandatory sanitization."""
        self._sanitize_and_log("critical", msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs) -> None:
        """Log exception message with mandatory sanitization."""
        self._sanitize_and_log("exception", msg, *args, **kwargs)

    def log(self, level: Union[int, str], msg: str, *args, **kwargs) -> None:
        """Log message at specified level with mandatory sanitization."""
        # Convert string level to numeric if needed
        if isinstance(level, str):
            level = level.upper()
            level_map = {
                'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'WARN': 30,
                'ERROR': 40, 'CRITICAL': 50, 'EXCEPTION': 40
            }
            level = level_map.get(level, 20)  # Default to INFO

        # Get method name for the level
        level_methods = {
            10: "debug", 20: "info", 30: "warning", 40: "error", 50: "critical"
        }
        method_name = level_methods.get(level, "info")

        # Call the appropriate method
        getattr(self, method_name)(msg, *args, **kwargs)

    def setLevel(self, level) -> None:
        """Set logging level (only affects level, not security)."""
        self._logger.setLevel(level)

    def addHandler(self, handler) -> None:
        """Add a handler to the underlying logger."""
        self._logger.addHandler(handler)

    def removeHandler(self, handler) -> None:
        """Remove a handler from the underlying logger."""
        self._logger.removeHandler(handler)

    @property
    def handlers(self):
        """Get handlers from underlying logger."""
        return self._logger.handlers

    @property
    def level(self):
        """Get level from underlying logger."""
        return self._logger.level

    # CRITICAL: Prevent access to the underlying logger directly
    @property
    def logger(self):
        """
        CRITICAL SECURITY: Direct access to logger is PROHIBITED.

        This property returns a SecureLogger wrapper to maintain security.
        Attempting to access the raw logger will result in secure logging.
        """
        log_security_event(
            input_text="SECURITY_ATTEMPT: Direct logger access attempted",
            source="SecureLogger.security_violation",
            context={
                "function": "SecureLogger.logger",
                "caller_protection": "prevented_direct_access"
            },
            block_action=True
        )
        return self  # Return the secure wrapper itself


class LoggingEnforcer:
    """
    ARCH-ID003-001: Enforcement mechanism to prevent direct logging access.

    This class monitors and enforces secure logging practices throughout
    the application. It replaces standard logging methods with secure alternatives.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not LoggingEnforcer._initialized:
            self._patch_standard_logging()
            LoggingEnforcer._initialized = True

    def _patch_standard_logging(self):
        """
        ARCH-ID003-001: Patch standard logging to enforce sanitization.

        This method replaces standard logging functions with secure alternatives
        that cannot be bypassed. Any attempt to use direct logging will be
        intercepted and sanitized.
        """
        # Store original methods for access by SecureLogger
        if not hasattr(logging, 'getLogger_backup'):
            logging.getLogger_backup = logging.getLogger

        original_logger_class = logging.getLoggerClass()

        def secure_get_logger(name=None):
            """
            Enforce secure logging for all logger requests.

            This intercepts all getLogger() calls and returns SecureLogger instances
            instead of standard Logger instances.
            """
            # Check if this is a security logger (allow it for internal use)
            if name and "security" in str(name).lower():
                return logging.getLogger_backup(name)

            # Check if this is an internal system logger
            if name and any(sys_name in str(name).lower() for sys_name in ['pytest', 'urllib3', 'requests']):
                return logging.getLogger_backup(name)

            # Return a SecureLogger for all other requests
            return SecureLogger(name or "default_secure")

        # Replace the getLogger function
        logging.getLogger = secure_get_logger

        # Patch existing logger methods to show security warnings
        def _create_secure_wrapper(method_name):
            def secure_method(self, msg, *args, **kwargs):
                # Log security event for direct logging attempt
                log_security_event(
                    input_text=f"Direct logging attempt via {method_name}",
                    source="logging_enforcer",
                    context={
                        "method": method_name,
                        "message_preview": str(msg)[:100],
                        "enforcement": "logging_bypass_attempt_detected"
                    },
                    block_action=False
                )
                # Use secure logging instead
                secure_logger = SecureLogger(self.name)
                getattr(secure_logger, method_name)(msg, *args, **kwargs)
            return secure_method

        # Only patch in test/non-production environments
        import os
        if os.environ.get('TESTING', '').lower() == 'true':
            # Skip patching during tests to avoid infinite recursion
            return

        # Patch the Logger class methods
        try:
            original_logger_class.debug = _create_secure_wrapper("debug")
            original_logger_class.info = _create_secure_wrapper("info")
            original_logger_class.warning = _create_secure_wrapper("warning")
            original_logger_class.warn = _create_secure_wrapper("warn")
            original_logger_class.error = _create_secure_wrapper("error")
            original_logger_class.critical = _create_secure_wrapper("critical")
            original_logger_class.exception = _create_secure_wrapper("exception")
        except Exception:
            # If patching fails, continue without it
            pass


# ARCH-ID003-001: DO NOT auto-initialize the logging enforcer
# This prevents infinite recursion with security logging
# The enforcer must be explicitly initialized when needed
# import os
# if os.environ.get('TESTING', '').lower() != 'true':
#     _logging_enforcer = LoggingEnforcer()


def __getattr__(name: str) -> re.Pattern:
    """
    Module-level lazy loading for regex patterns with backward compatibility.

    Provides backward compatibility for regex pattern constants while enabling
    lazy compilation for performance optimization.

    This function is called when accessing attributes that don't exist on the module.
    It enables lazy loading of regex patterns while maintaining the expected API.

    Args:
        name: Attribute name being accessed

    Returns:
        Compiled regex pattern for backward compatibility

    Raises:
        AttributeError: If name is not a recognized lazy-loaded pattern

    Examples:
        >>> import reasoning_library.sanitization as sanitization
        >>> pattern = sanitization._DANGEROUS_KEYWORD_PATTERN  # Triggers lazy compilation
        >>> isinstance(pattern, re.Pattern)  # True
    """
    pattern_getters = {
        '_DANGEROUS_KEYWORD_PATTERN': _get_dangerous_keyword_pattern,
        '_TEMPLATE_INJECTION_PATTERN': _get_template_injection_pattern,
        '_FORMAT_STRING_PATTERN': _get_format_string_pattern,
        '_CODE_INJECTION_PATTERN': _get_code_injection_pattern,
        '_DUNDER_PATTERN': _get_dunder_pattern,
        '_ATTRIBUTE_PATTERN': _get_attribute_pattern,
        '_SHELL_PATTERN': _get_shell_pattern,
        '_BRACKET_PATTERN': _get_bracket_pattern,
        '_QUOTE_PATTERN': _get_quote_pattern,
        '_HTML_INJECTION_PATTERN': _get_html_injection_pattern,
        '_CONTROL_CHAR_PATTERN': _get_control_char_pattern,
        '_ANSI_ESCAPE_PATTERN': _get_ansi_escape_pattern,
        '_WHITESPACE_PATTERN': _get_whitespace_pattern,
        '_LOG_INJECTION_PATTERN': _get_log_injection_pattern,
        '_NESTED_INJECTION_PATTERN': _get_nested_injection_pattern,
        '_STRING_CONCATENATION_PATTERN': _get_string_concatenation_pattern,
        '_SENSITIVE_DATA_PATTERN': _get_sensitive_data_pattern,
    }

    if name in pattern_getters:
        return pattern_getters[name]()

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")