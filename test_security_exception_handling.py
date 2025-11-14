#!/usr/bin/env python3
"""
Test script to validate secure exception handling for security workflows.

This script tests the JSON parsing logic that appears in the GitHub security workflow
to ensure proper exception handling that doesn't mask security vulnerabilities.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch, mock_open
from typing import Any, Dict


class SecurityWorkflowExceptionHandlingTest(unittest.TestCase):
    """Test secure exception handling for security workflow JSON parsing."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_json_data = {
            "vulnerabilities": [
                {
                    "name": "test-vuln",
                    "version": "1.0.0",
                    "description": "Test vulnerability"
                }
            ]
        }

        self.valid_bandit_data = {
            "results": [
                {
                    "issue_confidence": "high",
                    "issue_severity": "high",
                    "test_name": "hardcoded_password"
                }
            ]
        }

        self.valid_semgrep_data = {
            "results": [
                {
                    "rule_id": "python.flask.security.disabled-debug",
                    "message": "Debug mode should not be enabled in production"
                }
            ]
        }

        self.valid_license_data = [
            {
                "name": "test-package",
                "version": "1.0.0",
                "License": "MIT"
            },
            {
                "name": "gpl-package",
                "version": "2.0.0",
                "License": "GPL-3.0"
            }
        ]

    def test_pip_audit_json_parsing_with_invalid_json(self):
        """Test pip-audit JSON parsing handles malformed JSON gracefully."""
        # This simulates the bare except on line 90 of security.yml

        # Test with malformed JSON
        malformed_json = '{"vulnerabilities": ['

        with patch('builtins.open', mock_open(read_data=malformed_json)):
            with patch('os.path.exists', return_value=True):
                # Original problematic code (what's currently in the workflow):
                try:
                    with open('pip-audit-report.json') as f:
                        data = json.load(f)
                        result = len(data.get('vulnerabilities', []))
                        print(f"Original code result: {result}")
                except:  # This is the bare except we need to fix
                    result = 0
                    print("Original code: bare except caught exception")

                # Should be 0 due to bare except masking the error
                self.assertEqual(result, 0)

    def test_pip_audit_json_parsing_with_specific_exceptions(self):
        """Test pip-audit JSON parsing with proper specific exception handling."""
        # This simulates the fixed version with specific exceptions

        # Test with malformed JSON
        malformed_json = '{"vulnerabilities": ['

        with patch('builtins.open', mock_open(read_data=malformed_json)):
            with patch('os.path.exists', return_value=True):
                # Fixed code with specific exceptions:
                try:
                    with open('pip-audit-report.json') as f:
                        data = json.load(f)
                        result = len(data.get('vulnerabilities', []))
                        print(f"Fixed code result: {result}")
                except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as e:
                    print(f"Fixed code: Specific exception caught: {type(e).__name__}: {e}")
                    result = 0
                except FileNotFoundError:
                    print("Fixed code: File not found (should be caught by os.path.exists check)")
                    result = 0
                except PermissionError:
                    print("Fixed code: Permission denied reading file")
                    result = 0

                # Should be 0 but with proper error logging
                self.assertEqual(result, 0)

    def test_safety_json_parsing_with_invalid_json(self):
        """Test safety JSON parsing handles malformed JSON gracefully."""
        # This simulates the bare except on line 119 of security.yml

        malformed_json = '{"vulnerabilities": ['

        with patch('builtins.open', mock_open(read_data=malformed_json)):
            with patch('os.path.exists', return_value=True):
                # Original problematic code:
                try:
                    with open('safety-report.json') as f:
                        data = json.load(f)
                        high_count = sum(1 for vuln in data.get('vulnerabilities', [])
                                       if vuln.get('severity', '').lower() in ['high', 'critical'])
                        result = high_count
                except:  # Bare except
                    result = 0

                self.assertEqual(result, 0)

    def test_safety_json_parsing_with_specific_exceptions(self):
        """Test safety JSON parsing with proper specific exception handling."""
        malformed_json = '{"vulnerabilities": ['

        with patch('builtins.open', mock_open(read_data=malformed_json)):
            with patch('os.path.exists', return_value=True):
                # Fixed code with specific exceptions:
                try:
                    with open('safety-report.json') as f:
                        data = json.load(f)
                        high_count = sum(1 for vuln in data.get('vulnerabilities', [])
                                       if vuln.get('severity', '').lower() in ['high', 'critical'])
                        result = high_count
                except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as e:
                    print(f"Safety parsing error: {type(e).__name__}: {e}")
                    result = 0
                except (FileNotFoundError, PermissionError) as e:
                    print(f"File access error: {type(e).__name__}: {e}")
                    result = 0

                self.assertEqual(result, 0)

    def test_bandit_json_parsing_with_invalid_json(self):
        """Test bandit JSON parsing handles malformed JSON gracefully."""
        # This simulates the bare except on line 194 of security.yml

        malformed_json = '{"results": ['

        with patch('builtins.open', mock_open(read_data=malformed_json)):
            with patch('os.path.exists', return_value=True):
                # Original problematic code:
                try:
                    with open('bandit-report.json') as f:
                        data = json.load(f)
                        high_count = sum(1 for result in data.get('results', [])
                                       if result.get('issue_confidence', '').lower() == 'high'
                                       and result.get('issue_severity', '').lower() in ['medium', 'high'])
                        result = high_count
                except:  # Bare except
                    result = 0

                self.assertEqual(result, 0)

    def test_bandit_json_parsing_with_specific_exceptions(self):
        """Test bandit JSON parsing with proper specific exception handling."""
        malformed_json = '{"results": ['

        with patch('builtins.open', mock_open(read_data=malformed_json)):
            with patch('os.path.exists', return_value=True):
                # Fixed code with specific exceptions:
                try:
                    with open('bandit-report.json') as f:
                        data = json.load(f)
                        high_count = sum(1 for result in data.get('results', [])
                                       if result.get('issue_confidence', '').lower() == 'high'
                                       and result.get('issue_severity', '').lower() in ['medium', 'high'])
                        result = high_count
                except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as e:
                    print(f"Bandit parsing error: {type(e).__name__}: {e}")
                    result = 0
                except (FileNotFoundError, PermissionError) as e:
                    print(f"File access error: {type(e).__name__}: {e}")
                    result = 0

                self.assertEqual(result, 0)

    def test_semgrep_json_parsing_with_invalid_json(self):
        """Test semgrep JSON parsing handles malformed JSON gracefully."""
        # This simulates the bare except on line 209 of security.yml

        malformed_json = '{"results": ['

        with patch('builtins.open', mock_open(read_data=malformed_json)):
            with patch('os.path.exists', return_value=True):
                # Original problematic code:
                try:
                    with open('semgrep-report.json') as f:
                        data = json.load(f)
                        result = len(data.get('results', []))
                except:  # Bare except
                    result = 0

                self.assertEqual(result, 0)

    def test_semgrep_json_parsing_with_specific_exceptions(self):
        """Test semgrep JSON parsing with proper specific exception handling."""
        malformed_json = '{"results": ['

        with patch('builtins.open', mock_open(read_data=malformed_json)):
            with patch('os.path.exists', return_value=True):
                # Fixed code with specific exceptions:
                try:
                    with open('semgrep-report.json') as f:
                        data = json.load(f)
                        result = len(data.get('results', []))
                except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as e:
                    print(f"Semgrep parsing error: {type(e).__name__}: {e}")
                    result = 0
                except (FileNotFoundError, PermissionError) as e:
                    print(f"File access error: {type(e).__name__}: {e}")
                    result = 0

                self.assertEqual(result, 0)

    def test_license_json_parsing_with_invalid_json(self):
        """Test license JSON parsing handles malformed JSON gracefully."""
        # This simulates the bare except on line 282 of security.yml

        malformed_json = '[{"name": "test"'

        with patch('builtins.open', mock_open(read_data=malformed_json)):
            with patch('os.path.exists', return_value=True):
                # Original problematic code:
                try:
                    with open('licenses.json') as f:
                        data = json.load(f)
                        risky = ['GPL', 'AGPL', 'LGPL', 'MPL']
                        risky_count = sum(1 for pkg in data
                                        if any(risk in pkg.get('License', '').upper()
                                              for risk in risky))
                        result = risky_count
                except:  # Bare except
                    result = 0

                self.assertEqual(result, 0)

    def test_license_json_parsing_with_specific_exceptions(self):
        """Test license JSON parsing with proper specific exception handling."""
        malformed_json = '[{"name": "test"'

        with patch('builtins.open', mock_open(read_data=malformed_json)):
            with patch('os.path.exists', return_value=True):
                # Fixed code with specific exceptions:
                try:
                    with open('licenses.json') as f:
                        data = json.load(f)
                        risky = ['GPL', 'AGPL', 'LGPL', 'MPL']
                        risky_count = sum(1 for pkg in data
                                        if any(risk in pkg.get('License', '').upper()
                                              for risk in risky))
                        result = risky_count
                except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as e:
                    print(f"License parsing error: {type(e).__name__}: {e}")
                    result = 0
                except (FileNotFoundError, PermissionError) as e:
                    print(f"File access error: {type(e).__name__}: {e}")
                    result = 0

                self.assertEqual(result, 0)

    def test_valid_json_parsing_still_works(self):
        """Test that valid JSON parsing still works correctly after our fixes."""
        # Test pip-audit parsing
        with patch('builtins.open', mock_open(read_data=json.dumps(self.valid_json_data))):
            with patch('os.path.exists', return_value=True):
                try:
                    with open('pip-audit-report.json') as f:
                        data = json.load(f)
                        result = len(data.get('vulnerabilities', []))
                except (json.JSONDecodeError, KeyError, TypeError, AttributeError, FileNotFoundError, PermissionError) as e:
                    result = 0

                self.assertEqual(result, 1)

        # Test safety parsing
        safety_data = {
            "vulnerabilities": [
                {"severity": "high", "name": "test-vuln"},
                {"severity": "low", "name": "low-vuln"}
            ]
        }

        with patch('builtins.open', mock_open(read_data=json.dumps(safety_data))):
            with patch('os.path.exists', return_value=True):
                try:
                    with open('safety-report.json') as f:
                        data = json.load(f)
                        high_count = sum(1 for vuln in data.get('vulnerabilities', [])
                                       if vuln.get('severity', '').lower() in ['high', 'critical'])
                        result = high_count
                except (json.JSONDecodeError, KeyError, TypeError, AttributeError, FileNotFoundError, PermissionError) as e:
                    result = 0

                self.assertEqual(result, 1)

    def test_keyboard_interrupt_not_masked(self):
        """Test that KeyboardInterrupt is NOT caught by our specific exceptions."""
        with patch('builtins.open', side_effect=KeyboardInterrupt()):
            with patch('os.path.exists', return_value=True):
                with self.assertRaises(KeyboardInterrupt):
                    try:
                        with open('pip-audit-report.json') as f:
                            data = json.load(f)
                            result = len(data.get('vulnerabilities', []))
                    except (json.JSONDecodeError, KeyError, TypeError, AttributeError, FileNotFoundError, PermissionError) as e:
                        result = 0

    def test_system_exit_not_masked(self):
        """Test that SystemExit is NOT caught by our specific exceptions."""
        with patch('builtins.open', side_effect=SystemExit(1)):
            with patch('os.path.exists', return_value=True):
                with self.assertRaises(SystemExit):
                    try:
                        with open('pip-audit-report.json') as f:
                            data = json.load(f)
                            result = len(data.get('vulnerabilities', []))
                    except (json.JSONDecodeError, KeyError, TypeError, AttributeError, FileNotFoundError, PermissionError) as e:
                        result = 0


if __name__ == '__main__':
    print("Testing security workflow exception handling...")
    print("=" * 60)
    unittest.main(verbosity=2)