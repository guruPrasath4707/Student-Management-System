"""Black-box input-validation tests for the terminal menu application."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_SCRIPT = REPO_ROOT / "Student Management System.py"


class TerminalValidationTests(unittest.TestCase):
    def run_cli(self, scripted_input: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory(prefix="student-management-test-") as temp_dir:
            return subprocess.run(
                [sys.executable, str(CLI_SCRIPT)],
                input=scripted_input,
                text=True,
                capture_output=True,
                cwd=temp_dir,
                timeout=10,
                check=False,
            )

    def test_blank_identity_is_rejected_without_crashing(self):
        result = self.run_cli("1\n  \nStudent Example\n13\n")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Roll number is required.", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_invalid_mark_is_rejected_without_crashing(self):
        result = self.run_cli("1\nS-01\nStudent Example\n10\n20\nnan\n40\n50\n13\n")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("must be a finite number", result.stdout)
        self.assertIn("Student was not added.", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_duplicate_roll_number_does_not_overwrite_existing_record(self):
        result = self.run_cli(
            "1\nS-02\nFirst Student\n10\n20\n30\n40\n50\n"
            "1\nS-02\nSecond Student\n13\n"
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("already exists", result.stdout)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
