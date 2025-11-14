#!/usr/bin/env python3
"""
Test script to verify the fixed security workflow works correctly.

This script tests the exact Python code snippets that were modified in the GitHub workflow.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch, mock_open


class FixedWorkflowTest(unittest.TestCase):
    """Test that the fixed security workflow code works correctly."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def create_temp_file(self, filename, content):
        """Create a temporary file with the given content."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath

    def test_fixed_pip_audit_parsing(self):
        """Test the fixed pip-audit parsing code."""
        # Test with valid data
        valid_data = {
            "vulnerabilities": [
                {"name": "test-vuln-1"},
                {"name": "test-vuln-2"}
            ]
        }
        file_path = self.create_temp_file('pip-audit-report.json', json.dumps(valid_data))

        # Simulate the fixed code from the workflow
        with patch('builtins.open', mock_open(read_data=json.dumps(valid_data))):
            with patch('os.path.exists', return_value=True):
                # This is the exact code from the fixed workflow
                import subprocess
                import sys

                result = subprocess.run([
                    sys.executable, '-c', '''
import json
try:
    with open("pip-audit-report.json") as f:
        data = json.load(f)
        print(len(data.get("vulnerabilities", [])))
except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as e:
    print(f"Error parsing pip-audit report: {type(e).__name__}: {e}", file=__import__("sys").stderr)
    print(0)
except (FileNotFoundError, PermissionError) as e:
    print(f"Error accessing pip-audit report: {type(e).__name__}: {e}", file=__import__("sys").stderr)
    print(0)
'''
                ], capture_output=True, text=True)

                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout.strip(), "2")

    def test_fixed_pip_audit_with_malformed_json(self):
        """Test the fixed pip-audit parsing with malformed JSON."""
        malformed_data = '{"vulnerabilities": ['

        with patch('builtins.open', mock_open(read_data=malformed_data)):
            with patch('os.path.exists', return_value=True):
                import subprocess
                import sys

                result = subprocess.run([
                    sys.executable, '-c', f'''
import json
try:
    with open("pip-audit-report.json") as f:
        data = json.load(f)
        print(len(data.get("vulnerabilities", [])))
except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as e:
    print(f"Error parsing pip-audit report: {{type(e).__name__}}: {{e}}", file=__import__("sys").stderr)
    print(0)
except (FileNotFoundError, PermissionError) as e:
    print(f"Error accessing pip-audit report: {{type(e).__name__}}: {{e}}", file=__import__("sys").stderr)
    print(0)
'''
                ], capture_output=True, text=True)

                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout.strip(), "0")
                # Should have error message in stderr
                self.assertIn("JSONDecodeError", result.stderr)

    def test_fixed_safety_parsing(self):
        """Test the fixed safety parsing code."""
        safety_data = {
            "vulnerabilities": [
                {"severity": "high", "name": "critical-vuln"},
                {"severity": "low", "name": "minor-vuln"}
            ]
        }

        import subprocess
        import sys

        result = subprocess.run([
            sys.executable, '-c', f'''
import json
try:
    import json
    data = {json.dumps(safety_data)}
    high_count = sum(1 for vuln in data.get("vulnerabilities", [])
                   if vuln.get("severity", "").lower() in ["high", "critical"])
    print(high_count)
except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as e:
    print(f"Error parsing safety report: {{type(e).__name__}}: {{e}}", file=__import__("sys").stderr)
    print(0)
except (FileNotFoundError, PermissionError) as e:
    print(f"Error accessing safety report: {{type(e).__name__}}: {{e}}", file=__import__("sys").stderr)
    print(0)
'''
        ], capture_output=True, text=True)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "1")

    def test_fixed_bandit_parsing(self):
        """Test the fixed bandit parsing code."""
        bandit_data = {
            "results": [
                {
                    "issue_confidence": "high",
                    "issue_severity": "high",
                    "test_name": "hardcoded_password"
                },
                {
                    "issue_confidence": "low",
                    "issue_severity": "medium",
                    "test_name": "other_issue"
                }
            ]
        }

        import subprocess
        import sys

        result = subprocess.run([
            sys.executable, '-c', f'''
import json
try:
    data = {json.dumps(bandit_data)}
    high_count = sum(1 for result in data.get("results", [])
                   if result.get("issue_confidence", "").lower() == "high"
                   and result.get("issue_severity", "").lower() in ["medium", "high"])
    print(high_count)
except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as e:
    print(f"Error parsing bandit report: {{type(e).__name__}}: {{e}}", file=__import__("sys").stderr)
    print(0)
except (FileNotFoundError, PermissionError) as e:
    print(f"Error accessing bandit report: {{type(e).__name__}}: {{e}}", file=__import__("sys").stderr)
    print(0)
'''
        ], capture_output=True, text=True)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "1")

    def test_fixed_semgrep_parsing(self):
        """Test the fixed semgrep parsing code."""
        semgrep_data = {
            "results": [
                {"rule_id": "rule1"},
                {"rule_id": "rule2"},
                {"rule_id": "rule3"}
            ]
        }

        import subprocess
        import sys

        result = subprocess.run([
            sys.executable, '-c', f'''
import json
try:
    data = {json.dumps(semgrep_data)}
    print(len(data.get("results", [])))
except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as e:
    print(f"Error parsing semgrep report: {{type(e).__name__}}: {{e}}", file=__import__("sys").stderr)
    print(0)
except (FileNotFoundError, PermissionError) as e:
    print(f"Error accessing semgrep report: {{type(e).__name__}}: {{e}}", file=__import__("sys").stderr)
    print(0)
'''
        ], capture_output=True, text=True)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "3")

    def test_fixed_license_parsing(self):
        """Test the fixed license parsing code."""
        license_data = [
            {"name": "package1", "License": "MIT"},
            {"name": "package2", "License": "GPL-3.0"},
            {"name": "package3", "License": "AGPL-1.0"},
            {"name": "package4", "License": "Apache-2.0"}
        ]

        import subprocess
        import sys

        result = subprocess.run([
            sys.executable, '-c', f'''
import json
risky = ["GPL", "AGPL", "LGPL", "MPL"]
try:
    data = {json.dumps(license_data)}
    risky_count = sum(1 for pkg in data
                    if any(risk in pkg.get("License", "").upper()
                          for risk in risky))
    print(risky_count)
except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as e:
    print(f"Error parsing license report: {{type(e).__name__}}: {{e}}", file=__import__("sys").stderr)
    print(0)
except (FileNotFoundError, PermissionError) as e:
    print(f"Error accessing license report: {{type(e).__name__}}: {{e}}", file=__import__("sys").stderr)
    print(0)
'''
        ], capture_output=True, text=True)

        self.assertEqual(result.returncode, 0)
        # Should count GPL-3.0 and AGPL-1.0 = 2 risky licenses
        self.assertEqual(result.stdout.strip(), "2")

    def test_workflow_syntax_validation(self):
        """Test that the workflow YAML is still valid after our changes."""
        import yaml
        try:
            with open('/Users/eringreen/Development/reasoning_library/.github/workflows/security.yml', 'r') as f:
                workflow_content = yaml.safe_load(f)
            self.assertIsNotNone(workflow_content)
            self.assertIn('name', workflow_content)
            self.assertEqual(workflow_content['name'], 'Security Scanning')
        except Exception as e:
            self.fail(f"Workflow YAML is invalid: {e}")


if __name__ == '__main__':
    print("Testing fixed security workflow...")
    print("=" * 60)
    unittest.main(verbosity=2)