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
    insert_student_records,
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
    def create_database(self, path: Path, roll_number: str, name: str, marks=(10, 20, 30, 40, 50), average=30) -> None:
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
                (roll_number, name, *marks, average),
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


    def test_upgrades_legacy_schema_recomputes_averages_and_sets_version(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            source = base / "legacy.db"
            target = base / "app.db"
            self.create_database(
                source, "S-STALE", "Legacy Student", marks=(10, 20, 30, 40, 50), average=99
            )

            connection = connect_database(target, legacy_path=source)
            try:
                self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 1)
                row = connection.execute(
                    "SELECT roll_number, name, marks_subject1, marks_subject2, "
                    "marks_subject3, marks_subject4, marks_subject5, average_marks "
                    "FROM students"
                ).fetchone()
                self.assertEqual(row, ("S-STALE", "Legacy Student", 10.0, 20.0, 30.0, 40.0, 50.0, 30.0))
                schema_sql = connection.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name='students'"
                ).fetchone()[0].lower()
                self.assertIn("check", schema_sql)
                self.assertIn("not null", schema_sql)
            finally:
                connection.close()

            with sqlite3.connect(source) as original:
                self.assertEqual(
                    original.execute("SELECT average_marks FROM students").fetchone()[0], 99
                )
                self.assertEqual(original.execute("PRAGMA user_version").fetchone()[0], 0)

    def test_constrained_database_rejects_invalid_direct_writes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "app.db"
            connection = connect_database(target)
            try:
                valid_marks = (10, 20, 30, 40, 50)
                invalid_rows = [
                    ("", "Name", *valid_marks, 30),
                    ("S-EMPTY-NAME", "   ", *valid_marks, 30),
                    ("S-LOW", "Name", -1, 20, 30, 40, 50, 27.8),
                    ("S-HIGH", "Name", 10, 20, 30, 40, 101, 40.2),
                    ("S-AVG", "Name", *valid_marks, 31),
                ]
                for row in invalid_rows:
                    with self.subTest(row=row):
                        with self.assertRaises(sqlite3.IntegrityError):
                            connection.execute(
                                "INSERT INTO students VALUES (?, ?, ?, ?, ?, ?, ?, ?)", row
                            )
                        connection.rollback()
            finally:
                connection.close()

    def test_invalid_legacy_record_is_not_discarded_during_upgrade(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            source = base / "legacy-invalid.db"
            target = base / "app.db"
            self.create_database(
                source, "S-INVALID", "Broken Record", marks=(10, 20, 30, 40, 101), average=40.2
            )

            with self.assertRaisesRegex(StorageError, "student record 1"):
                connect_database(target, legacy_path=source)

            with sqlite3.connect(source) as original:
                self.assertEqual(
                    original.execute("SELECT marks_subject5 FROM students").fetchone()[0], 101
                )
            self.assertTrue(target.exists())
            with sqlite3.connect(target) as copied:
                self.assertEqual(
                    copied.execute("SELECT marks_subject5 FROM students").fetchone()[0], 101
                )
                self.assertEqual(copied.execute("PRAGMA user_version").fetchone()[0], 0)

    def test_null_identity_fields_are_rejected_by_core_validator(self):
        from student_core import validate_student_identity
        for roll_number, name in ((None, "Name"), ("S-NULL-NAME", None)):
            with self.subTest(roll_number=roll_number, name=name):
                with self.assertRaises(ValueError):
                    validate_student_identity(roll_number, name)


    def test_bulk_insert_recomputes_averages_and_commits_all_rows(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            connection = connect_database(Path(temp_dir) / "app.db")
            try:
                inserted = insert_student_records(
                    connection,
                    [
                        ("S-A", "Student A", 10, 20, 30, 40, 50, 999),
                        ("S-B", "Student B", 100, 90, 80, 70, 60, -20),
                    ],
                )
                self.assertEqual(inserted, 2)
                rows = connection.execute(
                    "SELECT roll_number, average_marks FROM students ORDER BY roll_number"
                ).fetchall()
                self.assertEqual(rows, [("S-A", 30.0), ("S-B", 80.0)])
            finally:
                connection.close()

    def test_bulk_insert_rolls_back_the_whole_batch_on_duplicate_key(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            connection = connect_database(Path(temp_dir) / "app.db")
            try:
                insert_student_records(
                    connection, [("S-EXISTS", "Keep This Record", 1, 2, 3, 4, 5, 3)]
                )
                with self.assertRaises(sqlite3.IntegrityError):
                    insert_student_records(
                        connection,
                        [
                            ("S-NEW", "Must Roll Back", 10, 20, 30, 40, 50, 30),
                            ("S-EXISTS", "Duplicate", 20, 30, 40, 50, 60, 40),
                        ],
                    )
                rows = connection.execute(
                    "SELECT roll_number, name FROM students ORDER BY roll_number"
                ).fetchall()
                self.assertEqual(rows, [("S-EXISTS", "Keep This Record")])
            finally:
                connection.close()

    def test_bulk_insert_validates_batch_before_any_database_write(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            connection = connect_database(Path(temp_dir) / "app.db")
            try:
                with self.assertRaisesRegex(ValueError, "Record 2"):
                    insert_student_records(
                        connection,
                        [
                            ("S-VALID", "Valid", 10, 20, 30, 40, 50, 30),
                            ("S-INVALID", "Invalid", 10, 20, 30, 40, 101, 40),
                        ],
                    )
                self.assertEqual(
                    connection.execute("SELECT COUNT(*) FROM students").fetchone()[0], 0
                )
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
