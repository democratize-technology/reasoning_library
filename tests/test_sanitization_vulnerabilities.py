"""
Test for input validation bypass vulnerabilities in the sanitization module.

These tests demonstrate critical security vulnerabilities that could allow injection attacks.
All these tests should FAIL initially to demonstrate the vulnerabilities.
"""

import pytest

from reasoning_library.sanitization import (
    sanitize_text_input,
    sanitize_for_concatenation,
    sanitize_for_display,
    SanitizationLevel
)


def test_case_bypass_vulnerability():
    """
    VULNERABILITY: Case sensitivity bypass allows dangerous keywords to evade detection.

    Expected behavior: All case variations of dangerous keywords should be blocked.
    Current behavior: Some case variations bypass sanitization.
    """
    # Test case variations that should be blocked but might bypass
    case_bypass_attempts = [
        "IMPORT os",  # Uppercase
        "Import os",  # Title case
        "iMpOrT os",  # Mixed case
        "IMPORT('module')",  # Uppercase with parentheses
        "EVAL('code')",  # Uppercase eval
        "EXEC('command')",  # Uppercase exec
        "SYSTEM('command')",  # Uppercase system
        "SUBPROCESS.run()",  # Title case
        "CONFIG.get()",  # Title case
        "GLOBALS()",  # Uppercase
        "LOCALS()",  # Uppercase
        "VARS()",  # Uppercase
        "DIR()",  # Uppercase
        "GETATTR(obj, 'attr')",  # Title case
        "SETATTR(obj, 'attr', 'val')",  # Title case
    ]

    for attempt in case_bypass_attempts:
        result = sanitize_text_input(attempt, level=SanitizationLevel.STRICT)
        # This should FAIL initially - dangerous case variations are not properly blocked
        assert not any(keyword in result.lower() for keyword in ['import', 'eval', 'exec', 'system', 'subprocess']), \
            f"Case bypass vulnerability: {attempt} -> {result}"


def test_unicode_obfuscation_bypass():
    """
    VULNERABILITY: Unicode characters can bypass ASCII-based regex patterns.

    Expected behavior: Unicode lookalike characters should be normalized or blocked.
    Current behavior: Unicode obfuscation can bypass pattern matching.
    """
    # Unicode obfuscation attempts
    unicode_bypass_attempts = [
        "ｉｍｐｏｒｔ os",  # Full-width Unicode characters
        "ｅｖａｌ('code')",  # Full-width eval
        "ｅｘｅｃ('command')",  # Full-width exec
        "imp\u0301ort os",  # Combining characters
        "eva\u0301l('code')",  # Combining accent
        "exe\u0301c('command')",  # Combining accent
        "import\u200b os",  # Zero-width space
        "eval\u200b('code')",  # Zero-width space
        "exec\u200b('command')",  # Zero-width space
        "import\u202e os",  # Right-to-left override
        "import\u202d os",  # Left-to-right override
        "import\u200c os",  # Zero-width non-joiner
        "import\u200d os",  # Zero-width joiner
    ]

    for attempt in unicode_bypass_attempts:
        result = sanitize_text_input(attempt, level=SanitizationLevel.STRICT)
        # This should FAIL initially - Unicode obfuscation is not properly handled
        assert not any(keyword in result.lower() for keyword in ['import', 'eval', 'exec']), \
            f"Unicode bypass vulnerability: {attempt} -> {result}"


def test_nested_injection_bypass():
    """
    VULNERABILITY: Nested/encoded injection patterns can bypass simple regex matching.

    Expected behavior: Nested and encoded injection attempts should be detected.
    Current behavior: Complex nesting can evade detection.
    """
    # Nested injection attempts
    nested_bypass_attempts = [
        "eval('eval(\"code\")')",  # Nested eval
        "exec('exec(\"command\")')",  # Nested exec
        "eval('__import__(\"os\")')",  # Eval with import
        "exec('eval(\"import os\")')",  # Exec with eval and import
        "eval(chr(101)+chr(118)+chr(97)+chr(108)+\"('code')\")",  # Character encoding
        "eval('e'+'v'+'a'+'l'+'(\"code\")')",  # String concatenation
        "eval('e\x76a\x6c(\"code\")')",  # Hex encoding
        "eval('e\\\\166a\\\\154(\"code\")')",  # Octal encoding
        "__import__('o'+'s')",  # String concatenation in import
        "__import__('\\x6f\\x73')",  # Hex in import
        "getattr(__import__('os'), 'system')('command')",  # Complex chaining
    ]

    for attempt in nested_bypass_attempts:
        result = sanitize_text_input(attempt, level=SanitizationLevel.STRICT)
        # This should FAIL initially - nested injections are not properly detected
        assert 'BLOCKED' in result or not any(keyword in result.lower() for keyword in ['eval', 'exec', '__import__']), \
            f"Nested injection bypass: {attempt} -> {result}"


def test_template_injection_bypass():
    """
    VULNERABILITY: Template injection patterns can be bypassed using alternative syntax.

    Expected behavior: All template injection syntax should be blocked.
    Current behavior: Alternative template syntax can bypass detection.
    """
    # Template injection bypass attempts
    template_bypass_attempts = [
        "{{user_input}}",  # Jinja2 style
        "#{user_input}",  # Ruby style
        "${{user_input}}",  # Double template
        "$ {user_input}",  # Space in template
        "${user_input}",  # Space in template
        "${{7*7}}",  # Math in template
        "{{7*7}}",  # Jinja2 math
        "#{7*7}",  # Ruby math
        "{{config.items()}}",  # Jinja2 config access
        "{{''.__class__.__mro__[2].__subclasses__()}}",  # Jinja2 RCE
        "${T(java.lang.Runtime).getRuntime().exec('cmd')}",  # Spring EL injection
    ]

    for attempt in template_bypass_attempts:
        result = sanitize_text_input(attempt, level=SanitizationLevel.STRICT)
        # This should FAIL initially - alternative template syntax is not properly blocked
        assert '{' not in result and '}' not in result, \
            f"Template injection bypass: {attempt} -> {result}"


def test_format_string_bypass():
    """
    VULNERABILITY: Format string patterns can be bypassed using alternative syntax.

    Expected behavior: All format string variations should be blocked.
    Current behavior: Complex format string patterns can bypass detection.
    """
    # Format string bypass attempts
    format_bypass_attempts = [
        "%(user_input)s",  # Named format string
        "%{user_input}s",  # Alternative syntax
        "%1$s",  # Positional format
        "%(name)s %(value)d",  # Multiple named formats
        "{user_input}".format(user_input="value"),  # .format() method
        f"{user_input}",  # f-string (though this would be executed before sanitization)
        "%.100s",  # Precision format
        "%*.*s",  # Variable precision
        "%c%c%c%c",  # Character format (can build strings)
    ]

    for attempt in format_bypass_attempts:
        result = sanitize_text_input(attempt, level=SanitizationLevel.STRICT)
        # This should FAIL initially - complex format strings are not properly blocked
        assert '%' not in result or result.count('%') < attempt.count('%'), \
            f"Format string bypass: {attempt} -> {result}"


def test_attribute_access_bypass():
    """
    VULNERABILITY: Attribute access patterns can be bypassed using alternative syntax.

    Expected behavior: All dangerous attribute access should be blocked.
    Current behavior: Complex attribute access patterns can bypass detection.
    """
    # Attribute access bypass attempts
    attribute_bypass_attempts = [
        "__builtins__.__import__",  # Builtins access
        "__import__",  # Dunder method
        "globals()['os']",  # Globals access
        "locals()['os']",  # Locals access
        "vars()['os']",  # Vars access
        "dir(__builtins__)",  # Builtins inspection
        "getattr(__builtins__, '__import__')",  # Dynamic attribute access
        "setattr(obj, 'attr', 'val')",  # Dynamic attribute setting
        "delattr(obj, 'attr')",  # Dynamic attribute deletion
        "hasattr(obj, 'attr')",  # Attribute checking
        "obj.__class__.__bases__",  # Class hierarchy access
        "obj.__subclasses__()",  # Subclass access
    ]

    for attempt in attribute_bypass_attempts:
        result = sanitize_text_input(attempt, level=SanitizationLevel.STRICT)
        # This should FAIL initially - complex attribute access is not properly blocked
        assert '__' not in result or 'BLOCKED' in result, \
            f"Attribute access bypass: {attempt} -> {result}"


def test_shell_metacharacter_bypass():
    """
    VULNERABILITY: Shell metacharacter detection can be bypassed using encoding.

    Expected behavior: All shell metacharacters should be blocked.
    Current behavior: Encoded metacharacters can bypass detection.
    """
    # Shell metacharacter bypass attempts
    shell_bypass_attempts = [
        "$(whoami)",  # Command substitution
        "`whoami`",  # Backtick command
        "|cat /etc/passwd",  # Pipe
        "&& rm -rf /",  # AND operator
        "|| rm -rf /",  # OR operator
        "; rm -rf /",  # Command separator
        "> /etc/passwd",  # Redirect
        ">> /etc/passwd",  # Append redirect
        "< /etc/passwd",  # Input redirect
        "2>&1",  # File descriptor redirect
        "\\$(whoami)",  # Escaped substitution
        "\\`whoami\\`",  # Escaped backticks
    ]

    for attempt in shell_bypass_attempts:
        result = sanitize_text_input(attempt, level=SanitizationLevel.STRICT)
        # This should FAIL initially - shell metacharacters are not properly blocked
        assert not any(char in result for char in ['$', '`', '|', '&', ';', '>', '<']), \
            f"Shell metacharacter bypass: {attempt} -> {result}"


def test_control_character_bypass():
    """
    VULNERABILITY: Control character detection can be bypassed using alternative encodings.

    Expected behavior: All control characters should be normalized.
    Current behavior: Alternative control character encodings can bypass detection.
    """
    # Control character bypass attempts
    control_bypass_attempts = [
        "text\u000bwith\u000ccontrol\u000dchars",  # Vertical tab, form feed, carriage return
        "text\x0bwith\x0ccontrol\x0dchars",  # Hex control chars
        "text\u2028with\u2029control\u200bchars",  # Unicode line/paragraph separators
        "text\x85with\x200E\x200Fcontrol\x2060chars",  # Unicode control chars
        "text\\nwith\\r\\tcontrol\\x0achars",  # Escaped control chars
        "text\\\\nwith\\\\r\\\\tcontrol\\\\x0achars",  # Double-escaped
        "text\nwith\rlog\ninjection\t\ttabs",  # Mixed control chars
        "ERROR\x1b[31m [INJECTION]\x1b[0m",  # ANSI injection
    ]

    for attempt in control_bypass_attempts:
        result = sanitize_for_logging(attempt)  # Use logging-specific function
        # This should FAIL initially - control characters are not properly normalized
        assert '\n' not in result and '\r' not in result and '\t' not in result, \
            f"Control character bypass: {repr(attempt)} -> {repr(result)}"


if __name__ == "__main__":
    print("🧪 Running input validation bypass vulnerability tests...")
    print("❌ These tests are EXPECTED TO FAIL to demonstrate vulnerabilities")
    print("🔍 After fixing vulnerabilities, these tests should PASS")

    # Run all vulnerability tests
    pytest.main([__file__, "-v"])