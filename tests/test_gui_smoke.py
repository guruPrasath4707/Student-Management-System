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


# Exercise the recovery path without exposing sample values in logs. The synthetic
# fixture contains a blank legacy identifier; the test repairs it through the UI.
GUI_REPAIR_SCRIPT = r"""
import runpy
import sys
import tkinter as tk
from tkinter import messagebox

original_mainloop = tk.Misc.mainloop
def smoke_mainloop(self, n=0):
    app_globals = sys._getframe(1).f_globals
    def repair_selected_row():
        tree = app_globals["student_tree"]
        rows = tree.get_children()
        if len(rows) != 1:
            raise AssertionError(f"Expected one synthetic row, found {len(rows)}")
        tree.selection_set(rows[0])
        app_globals["load_selected_student"]()
        roll_entry = app_globals["entry_roll"]
        roll_entry.delete(0, "end")
        roll_entry.insert(0, "S-REPAIRED")
        app_globals["update_student"]()
        print("GUI_LEGACY_ROW_REPAIRED")

    self.after(100, repair_selected_row)
    self.after(500, self.destroy)
    return original_mainloop(self, n)

tk.Misc.mainloop = smoke_mainloop
messagebox.showwarning = lambda *args, **kwargs: print("LEGACY_REVIEW_WARNING_SHOWN")
messagebox.showinfo = lambda *args, **kwargs: None
messagebox.showerror = lambda *args, **kwargs: print("GUI_ERROR")
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

    def test_blank_legacy_identifier_is_repaired_and_schema_upgrade_completes(self):
        with tempfile.TemporaryDirectory(prefix="student-management-repair-") as temp_dir:
            base = Path(temp_dir)
            working_dir = base / "working"
            working_dir.mkdir()
            data_dir = base / "app-data"
            data_dir.mkdir()
            legacy_path = working_dir / DATABASE_FILENAME
            database_path = data_dir / DATABASE_FILENAME

            with closing(sqlite3.connect(legacy_path)) as legacy:
                legacy.execute("""
                    CREATE TABLE students (
                        roll_number TEXT PRIMARY KEY,
                        name TEXT,
                        marks_subject1 REAL,
                        marks_subject2 REAL,
                        marks_subject3 REAL,
                        marks_subject4 REAL,
                        marks_subject5 REAL,
                        average_marks REAL
                    )
                """)
                legacy.execute(
                    "INSERT INTO students VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (None, "Synthetic Legacy Row", 10, 20, 30, 40, 50, 30),
                )
                legacy.commit()

            environment = os.environ.copy()
            environment["STUDENT_MANAGEMENT_DATA_DIR"] = str(data_dir)
            repair_run = subprocess.run(
                [sys.executable, "-c", GUI_REPAIR_SCRIPT],
                cwd=working_dir,
                env=environment,
                text=True,
                capture_output=True,
                timeout=15,
                check=False,
            )
            self.assertEqual(
                repair_run.returncode, 0,
                msg=f"stdout:\n{repair_run.stdout}\nstderr:\n{repair_run.stderr}",
            )
            self.assertIn("LEGACY_REVIEW_WARNING_SHOWN", repair_run.stdout)
            self.assertIn("GUI_LEGACY_ROW_REPAIRED", repair_run.stdout)
            self.assertNotIn("GUI_ERROR", repair_run.stdout)

            with closing(sqlite3.connect(database_path)) as repaired:
                self.assertEqual(repaired.execute("PRAGMA user_version").fetchone()[0], 0)
                self.assertEqual(
                    repaired.execute(
                        "SELECT roll_number, name, marks_subject5, average_marks FROM students"
                    ).fetchone(),
                    ("S-REPAIRED", "Synthetic Legacy Row", 50.0, 30.0),
                )

            # A normal subsequent launch should now be able to finish the constrained upgrade.
            upgrade_run = subprocess.run(
                [sys.executable, "-c", GUI_SMOKE_SCRIPT],
                cwd=working_dir,
                env=environment,
                text=True,
                capture_output=True,
                timeout=15,
                check=False,
            )
            self.assertEqual(
                upgrade_run.returncode, 0,
                msg=f"stdout:\n{upgrade_run.stdout}\nstderr:\n{upgrade_run.stderr}",
            )
            with closing(sqlite3.connect(database_path)) as upgraded:
                self.assertEqual(upgraded.execute("PRAGMA user_version").fetchone()[0], 1)
                self.assertEqual(upgraded.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                self.assertEqual(
                    upgraded.execute(
                        "SELECT roll_number, average_marks FROM students"
                    ).fetchone(),
                    ("S-REPAIRED", 30.0),
                )

            # The source file remains untouched while the repaired copy becomes the active store.
            with closing(sqlite3.connect(legacy_path)) as original:
                self.assertIsNone(original.execute("SELECT roll_number FROM students").fetchone()[0])


if __name__ == "__main__":
    unittest.main()
