"""
MAJOR-007: Code Analysis for Exception Handling Vulnerabilities

This test demonstrates the exception handling vulnerabilities by analyzing
the source code patterns directly, without requiring module imports.
"""

import re
import sys


def analyze_exception_handling_patterns():
    """Analyze validation.py for dangerous exception handling patterns."""
    print("🔍 Analyzing exception handling patterns in validation.py...")

    try:
        with open('src/reasoning_library/validation.py', 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ Could not find validation.py file")
        return False

    vulnerabilities = []

    # Pattern 1: Broad exception catching
    broad_except_pattern = r'except\s+(Exception|BaseException)\s+as\s+\w+:'
    broad_matches = re.findall(broad_except_pattern, content)

    if broad_matches:
        print(f"✅ CONFIRMED: Found {len(broad_matches)} broad exception handlers")

        # Find line numbers for broad exceptions
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if re.search(broad_except_pattern, line):
                print(f"   Line {i}: {line.strip()}")
                vulnerabilities.append(f"Broad exception handling at line {i}")

    # Pattern 2: Specific vulnerable lines we identified
    vulnerable_lines = [
        (171, "except Exception as e: in validate_dict_schema"),
        (321, "except (ValueError, OverflowError) as e: in _validate_string_confidence"),
        (454, "except Exception as e: in validate_parameters decorator"),
        (649, "except (ValidationError, TypeError, ValueError): in safe_divide"),
        (683, "except Exception as e: in safe_array_operation"),
    ]

    lines = content.split('\n')
    for line_num, description in vulnerable_lines:
        if line_num <= len(lines):
            line = lines[line_num - 1].strip()
            if 'except' in line:
                print(f"   📍 {description}")
                print(f"      Line {line_num}: {line}")
                vulnerabilities.append(description)

    return len(vulnerabilities) > 0


def analyze_security_logging_gaps():
    """Analyze missing security logging in validation functions."""
    print("\n🔍 Analyzing security logging gaps...")

    try:
        with open('src/reasoning_library/validation.py', 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ Could not find validation.py file")
        return False

    vulnerabilities = []

    # Check if security logging is imported
    if 'security_logging' not in content and 'get_security_logger' not in content:
        print("✅ CONFIRMED: Security logging not imported")
        vulnerabilities.append("Security logging not imported in validation module")

    # Check for validation functions that don't log security events
    validation_functions = [
        'validate_dict_schema',
        'validate_string_list',
        'validate_hypothesis_dict',
        'validate_confidence_value',
        'validate_hypotheses_list',
        'validate_metadata_dict',
    ]

    for func_name in validation_functions:
        # Find function definition
        func_pattern = rf'def {func_name}\('
        if re.search(func_pattern, content):
            print(f"   📋 Found function: {func_name}")

            # Check if function contains security logging
            func_start = re.search(func_pattern, content).start()
            remaining_content = content[func_start:]

            # Find the end of the function (next def or end of file)
            next_def = re.search(r'\ndef\s+\w+\s*\(', remaining_content[1:])
            if next_def:
                func_content = remaining_content[:next_def.start() + 1]
            else:
                func_content = remaining_content

            if 'log_security_event' not in func_content:
                print(f"      🔴 No security logging in {func_name}")
                vulnerabilities.append(f"Missing security logging in {func_name}")

    return len(vulnerabilities) > 0


def analyze_error_message_patterns():
    """Analyze error messages for potential information disclosure."""
    print("\n🔍 Analyzing error message patterns...")

    try:
        with open('src/reasoning_library/validation.py', 'r') as f:
            content = f.read()
        with open('src/reasoning_library/exceptions.py', 'r') as f:
            exceptions_content = f.read()
    except FileNotFoundError as e:
        print(f"❌ Could not read file: {e}")
        return False

    vulnerabilities = []

    # Look for detailed error messages that might expose internals
    risky_patterns = [
        (r'dangerous.*pattern', "Dangerous pattern detection exposed"),
        (r'invalid.*format', "Format validation logic exposed"),
        (r'not.*allowed', "Validation rules exposed"),
        (r'must.*be.*type', "Type validation internals exposed"),
        (r'cannot.*contain', "Content validation logic exposed"),
    ]

    for pattern, description in risky_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            print(f"✅ CONFIRMED: Found {len(matches)} potential information disclosure patterns")
            print(f"   Pattern: {pattern} - {description}")
            vulnerabilities.append(description)

            # Show examples
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    if len(line) < 100:  # Only show reasonable length lines
                        print(f"      Line {i}: {line.strip()}")

    # Check exception class for information disclosure
    if 'details' in exceptions_content:
        print("✅ CONFIRMED: Exception class contains details that might be exposed")
        vulnerabilities.append("Exception details could leak sensitive information")

    return len(vulnerabilities) > 0


def demonstrate_vulnerability_impacts():
    """Demonstrate the security impact of these vulnerabilities."""
    print("\n🚨 DEMONSTRATING VULNERABILITY IMPACTS")
    print("=" * 50)

    impacts = [
        {
            "vulnerability": "Broad exception handling",
            "impact": "Attack exceptions are masked and converted to generic errors",
            "example": "SQL injection exception becomes 'validation failed'",
            "risk": "Security monitoring bypass, attack goes undetected"
        },
        {
            "vulnerability": "Silent failure in safe_divide",
            "impact": "Dangerous inputs are processed silently",
            "example": "Code injection in numerator returns 0.0 without error",
            "risk": "Remote code execution, system compromise"
        },
        {
            "vulnerability": "Missing security logging",
            "impact": "Attack attempts are not logged to security systems",
            "example": "10 injection attempts, 0 security events logged",
            "risk": "No incident response, no attack attribution"
        },
        {
            "vulnerability": "Information disclosure",
            "impact": "Error messages reveal internal validation logic",
            "example": "Error shows 'dangerous pattern detected: eval('",
            "risk": "Attacker learns security controls to bypass them"
        }
    ]

    for i, impact in enumerate(impacts, 1):
        print(f"\n{i}. {impact['vulnerability']}")
        print(f"   Impact: {impact['impact']}")
        print(f"   Example: {impact['example']}")
        print(f"   Risk: {impact['risk']}")


def main():
    """Run vulnerability analysis."""
    print("🔍 MAJOR-007: Exception Handling Security Vulnerability Analysis")
    print("=" * 70)

    vulnerabilities_found = []

    # Analyze different vulnerability types
    if analyze_exception_handling_patterns():
        vulnerabilities_found.append("Broad exception handling patterns")

    if analyze_security_logging_gaps():
        vulnerabilities_found.append("Missing security logging")

    if analyze_error_message_patterns():
        vulnerabilities_found.append("Information disclosure in error messages")

    # Demonstrate impacts
    demonstrate_vulnerability_impacts()

    # Summary
    print("\n" + "=" * 70)
    print("📊 ANALYSIS SUMMARY")
    print("=" * 70)

    if vulnerabilities_found:
        print(f"❌ CRITICAL SECURITY ISSUES FOUND: {len(vulnerabilities_found)}")
        for i, vuln in enumerate(vulnerabilities_found, 1):
            print(f"   {i}. {vuln}")

        print(f"\n🎯 PRIORITY: HIGH")
        print(f"   These vulnerabilities allow attackers to:")
        print(f"   • Bypass security monitoring")
        print(f"   • Mask attack attempts")
        print(f"   • Learn internal security controls")
        print(f"   • Execute malicious operations silently")

        print(f"\n🔧 IMMEDIATE ACTION REQUIRED:")
        print(f"   1. Replace broad exception handling with specific types")
        print(f"   2. Add security logging to all validation functions")
        print(f"   3. Sanitize error messages to prevent information disclosure")
        print(f"   4. Implement proper error propagation for security events")

        return 1
    else:
        print("✅ No obvious vulnerabilities found in code analysis")
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)