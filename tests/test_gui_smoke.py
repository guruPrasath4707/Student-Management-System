"""Windows-only smoke test for constructing the maintained Tkinter application."""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from student_storage import DATABASE_FILENAME, connect_database

REPO_ROOT = Path(__file__).resolve().parents[1]

# CI's Windows 3.12 job has a desktop session. End the event loop automatically
# so a broken launch cannot hang the test runner indefinitely.
GUI_SMOKE_SCRIPT = r"""
import runpy
import tkinter as tk
from tkinter import messagebox

original_mainloop = tk.Misc.mainloop
def smoke_mainloop(self, n=0):
    self.after(150, self.destroy)
    return original_mainloop(self, n)

tk.Misc.mainloop = smoke_mainloop
messagebox.showwarning = lambda *args, **kwargs: None
runpy.run_path("Student.py", run_name="__main__")
"""


@unittest.skipUnless(
    sys.platform == "win32" and sys.version_info[:2] == (3, 12),
    "The Tkinter startup smoke test runs on the Windows/Python 3.12 CI job.",
)
class TkinterStartupSmokeTests(unittest.TestCase):
    def test_desktop_app_constructs_and_creates_valid_empty_database(self):
        with tempfile.TemporaryDirectory(prefix="student-management-gui-") as temp_dir:
            database_path = Path(temp_dir) / DATABASE_FILENAME
            # Create the current schema first, so the app does not migrate the
            # tracked legacy database from the repository directory.
            connection = connect_database(database_path)
            connection.close()

            environment = os.environ.copy()
            environment["STUDENT_MANAGEMENT_DATA_DIR"] = temp_dir
            result = subprocess.run(
                [sys.executable, "-c", GUI_SMOKE_SCRIPT],
                cwd=REPO_ROOT,
                env=environment,
                text=True,
                capture_output=True,
                timeout=15,
                check=False,
            )

            self.assertEqual(
                result.returncode,
                0,
                msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
            )

            self.assertTrue(database_path.is_file(), "The app did not create its user-data database.")
            with closing(sqlite3.connect(database_path)) as connection:
                self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 1)
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM students").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
