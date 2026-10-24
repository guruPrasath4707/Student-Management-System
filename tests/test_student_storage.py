"""Tests for application-data paths and non-destructive SQLite migration."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from student_storage import (
    DATABASE_FILENAME,
    APP_DIRECTORY_NAME,
    StorageError,
    connect_database,
    get_database_path,
)


class DatabasePathTests(unittest.TestCase):
    def test_respects_explicit_data_directory_override(self):
        path = get_database_path(
            env={"STUDENT_MANAGEMENT_DATA_DIR": "/custom/student-data"},
            home="/home/example",
            platform_name="linux",
        )
        self.assertEqual(path, Path("/custom/student-data") / DATABASE_FILENAME)

    def test_uses_windows_roaming_appdata(self):
        path = get_database_path(
            env={"APPDATA": "/profiles/example/Roaming"},
            home="/home/example",
            platform_name="win32",
        )
        self.assertEqual(
            path,
            Path("/profiles/example/Roaming") / APP_DIRECTORY_NAME / DATABASE_FILENAME,
        )

    def test_uses_xdg_data_home_on_linux(self):
        path = get_database_path(
            env={"XDG_DATA_HOME": "/home/example/.local/share"},
            home="/home/example",
            platform_name="linux",
        )
        self.assertEqual(
            path,
            Path("/home/example/.local/share") / APP_DIRECTORY_NAME / DATABASE_FILENAME,
        )

    def test_uses_macos_application_support(self):
        path = get_database_path(env={}, home="/Users/example", platform_name="darwin")
        self.assertEqual(
            path,
            Path("/Users/example/Library/Application Support")
            / APP_DIRECTORY_NAME
            / DATABASE_FILENAME,
        )


class DatabaseStorageTests(unittest.TestCase):
    def create_database(self, path: Path, roll_number: str, name: str) -> None:
        connection = sqlite3.connect(path)
        try:
            connection.execute("""
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
            connection.execute(
                "INSERT INTO students VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (roll_number, name, 10, 20, 30, 40, 50, 30),
            )
            connection.commit()
        finally:
            connection.close()

    def test_creates_database_and_schema_in_target_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "app-data" / DATABASE_FILENAME
            connection = connect_database(target)
            try:
                self.assertTrue(target.is_file())
                columns = {
                    row[1] for row in connection.execute("PRAGMA table_info(students)")
                }
                self.assertIn("roll_number", columns)
                self.assertIn("average_marks", columns)
            finally:
                connection.close()

    def test_migrates_legacy_database_without_changing_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            source = base / "legacy" / DATABASE_FILENAME
            target = base / "profile" / "app-data" / DATABASE_FILENAME
            source.parent.mkdir()
            self.create_database(source, "S-LEGACY", "Legacy Student")

            connection = connect_database(target, legacy_path=source)
            try:
                row = connection.execute(
                    "SELECT roll_number, name, average_marks FROM students"
                ).fetchone()
                self.assertEqual(row, ("S-LEGACY", "Legacy Student", 30.0))
                self.assertEqual(
                    connection.execute("PRAGMA integrity_check").fetchone()[0], "ok"
                )
            finally:
                connection.close()

            self.assertTrue(source.is_file(), "Migration must leave the source untouched.")
            with sqlite3.connect(source) as original:
                self.assertEqual(
                    original.execute("SELECT count(*) FROM students").fetchone()[0], 1
                )

    def test_existing_target_is_never_overwritten_by_legacy_migration(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            source = base / "legacy.db"
            target = base / "app.db"
            self.create_database(source, "S-OLD", "Old Record")
            self.create_database(target, "S-NEW", "Current Record")

            connection = connect_database(target, legacy_path=source)
            try:
                rows = connection.execute(
                    "SELECT roll_number, name FROM students"
                ).fetchall()
            finally:
                connection.close()
            self.assertEqual(rows, [("S-NEW", "Current Record")])

    def test_rejects_corrupt_legacy_file_without_creating_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            source = base / "legacy.db"
            target = base / "app.db"
            source.write_text("not a SQLite database", encoding="utf-8")

            with self.assertRaises(StorageError):
                connect_database(target, legacy_path=source)

            self.assertTrue(source.is_file())
            self.assertFalse(target.exists())
            self.assertEqual(list(base.glob("app.db.migration-*")), [])

    def test_refuses_to_migrate_a_database_with_an_unexpected_schema(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            source = base / "wrong-schema.db"
            target = base / "app.db"
            with sqlite3.connect(source) as connection:
                connection.execute("CREATE TABLE unrelated (id INTEGER PRIMARY KEY)")

            with self.assertRaisesRegex(StorageError, "no students table"):
                connect_database(target, legacy_path=source)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
