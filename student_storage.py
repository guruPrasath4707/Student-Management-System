"""Safe application-data location and one-time migration for the SQLite store."""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from collections.abc import Mapping

from student_core import calculate_average, parse_marks, validate_student_identity

DATABASE_FILENAME = "students_database.db"
APP_DIRECTORY_NAME = "StudentManagementSystem"
SCHEMA_VERSION = 1
REQUIRED_COLUMNS = {
    "roll_number",
    "name",
    "marks_subject1",
    "marks_subject2",
    "marks_subject3",
    "marks_subject4",
    "marks_subject5",
    "average_marks",
}


def _students_schema(table_name: str = "students") -> str:
    """Return the constrained schema for one of the internally named tables."""
    return f"""
    CREATE TABLE {table_name} (
        roll_number TEXT PRIMARY KEY NOT NULL
            CHECK(length(trim(roll_number)) > 0),
        name TEXT NOT NULL
            CHECK(length(trim(name)) > 0),
        marks_subject1 REAL NOT NULL
            CHECK(typeof(marks_subject1) IN ('integer', 'real') AND marks_subject1 BETWEEN 0 AND 100),
        marks_subject2 REAL NOT NULL
            CHECK(typeof(marks_subject2) IN ('integer', 'real') AND marks_subject2 BETWEEN 0 AND 100),
        marks_subject3 REAL NOT NULL
            CHECK(typeof(marks_subject3) IN ('integer', 'real') AND marks_subject3 BETWEEN 0 AND 100),
        marks_subject4 REAL NOT NULL
            CHECK(typeof(marks_subject4) IN ('integer', 'real') AND marks_subject4 BETWEEN 0 AND 100),
        marks_subject5 REAL NOT NULL
            CHECK(typeof(marks_subject5) IN ('integer', 'real') AND marks_subject5 BETWEEN 0 AND 100),
        average_marks REAL NOT NULL
            CHECK(
                typeof(average_marks) IN ('integer', 'real')
                AND average_marks BETWEEN 0 AND 100
                AND ABS(average_marks -
                    ((marks_subject1 + marks_subject2 + marks_subject3 +
                      marks_subject4 + marks_subject5) / 5.0)) < 0.00001
            )
    )
    """


STUDENTS_SCHEMA = _students_schema("students")

class StorageError(RuntimeError):
    """Raised when storage cannot be opened or safely migrated."""


def get_database_path(
    env: Mapping[str, str] | None = None,
    home: str | Path | None = None,
    platform_name: str | None = None,
) -> Path:
    """Return the user's app-data database path for Windows, macOS, or Linux."""
    environment = os.environ if env is None else env
    user_home = Path.home() if home is None else Path(home)
    platform_id = sys.platform if platform_name is None else platform_name

    override = environment.get("STUDENT_MANAGEMENT_DATA_DIR")
    if override:
        data_dir = Path(override).expanduser()
    elif platform_id.startswith("win"):
        base = environment.get("APPDATA")
        data_dir = Path(base).expanduser() if base else user_home / "AppData" / "Roaming"
        data_dir = data_dir / APP_DIRECTORY_NAME
    elif platform_id == "darwin":
        data_dir = user_home / "Library" / "Application Support" / APP_DIRECTORY_NAME
    else:
        xdg_data_home = environment.get("XDG_DATA_HOME")
        data_dir = (
            Path(xdg_data_home).expanduser() / APP_DIRECTORY_NAME
            if xdg_data_home
            else user_home / ".local" / "share" / APP_DIRECTORY_NAME
        )
    return data_dir / DATABASE_FILENAME


def _validate_legacy_schema(connection: sqlite3.Connection, source: Path) -> None:
    table = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='students'"
    ).fetchone()
    if table is None:
        raise StorageError(f"Cannot migrate {source}: no students table was found.")

    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(students)").fetchall()
    }
    missing = sorted(REQUIRED_COLUMNS - columns)
    extra = sorted(columns - REQUIRED_COLUMNS)
    if missing or extra:
        details = []
        if missing:
            details.append("missing columns: " + ", ".join(missing))
        if extra:
            details.append("unexpected columns: " + ", ".join(extra))
        raise StorageError(
            f"Cannot safely migrate {source}: " + "; ".join(details) + "."
        )


def _validate_current_schema(connection: sqlite3.Connection) -> None:
    """Refuse a schema-version marker that does not match the constrained schema."""
    _validate_legacy_schema(connection, Path("the current database"))
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='students'"
    ).fetchone()
    if row is None or not row[0]:
        raise StorageError("The current database is missing the students table definition.")

    normalized = "".join(row[0].lower().split())
    required_fragments = [
        "roll_numbertextprimarykeynotnull",
        "check(length(trim(roll_number))>0)",
        "nametextnotnull",
        "check(length(trim(name))>0)",
    ]
    for column in (
        "marks_subject1",
        "marks_subject2",
        "marks_subject3",
        "marks_subject4",
        "marks_subject5",
    ):
        required_fragments.append(
            f"check(typeof({column})in('integer','real')and{column}between0and100)"
        )
    required_fragments.append(
        "check(typeof(average_marks)in('integer','real')andaverage_marksbetween0and100"
        "andabs(average_marks-((marks_subject1+marks_subject2+marks_subject3+"
        "marks_subject4+marks_subject5)/5.0))<0.00001)"
    )
    if any(fragment not in normalized for fragment in required_fragments):
        raise StorageError(
            "The database marks its schema as current, but the table is missing required "
            "constraints. Back up the database and review its schema before continuing."
        )


def _upgrade_schema(connection: sqlite3.Connection) -> None:
    """Upgrade the original unconstrained table transactionally without dropping invalid data."""
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    table_exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='students'"
    ).fetchone() is not None

    if version > SCHEMA_VERSION:
        raise StorageError(
            f"The database schema version ({version}) is newer than this application supports "
            f"({SCHEMA_VERSION}). Upgrade the application before opening this database."
        )
    if version == SCHEMA_VERSION:
        if not table_exists:
            raise StorageError(
                "The database claims to use the current schema version but has no students table."
            )
        _validate_current_schema(connection)
        return

    if not table_exists:
        connection.execute(STUDENTS_SCHEMA)
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        connection.commit()
        return

    temporary_table = "students__migration_v1"
    unexpected_objects = connection.execute(
        "SELECT type, name FROM sqlite_master "
        "WHERE tbl_name='students' AND type IN ('trigger', 'index') "
        "AND name NOT LIKE 'sqlite_autoindex%'"
    ).fetchall()
    if unexpected_objects:
        raise StorageError(
            "Cannot safely upgrade the student table because custom indexes or triggers "
            "are attached. Back up the database and review those objects before migrating."
        )

    try:
        connection.execute("BEGIN IMMEDIATE")
        _validate_legacy_schema(connection, Path("the existing database"))
        rows = connection.execute(
            "SELECT roll_number, name, marks_subject1, marks_subject2, marks_subject3, "
            "marks_subject4, marks_subject5, average_marks FROM students"
        ).fetchall()

        normalized_rows = []
        seen_roll_numbers: set[str] = set()
        for row_number, row in enumerate(rows, start=1):
            try:
                roll_number, name = validate_student_identity(row[0], row[1])
                if roll_number in seen_roll_numbers:
                    raise ValueError("roll number duplicates another value after trimming")
                marks = parse_marks(row[2:7])
            except ValueError as exc:
                raise StorageError(
                    f"Cannot safely upgrade student record {row_number}: {exc} "
                    "No legacy records were deleted; back up and correct the record first."
                ) from exc
            average = calculate_average(marks)
            normalized_rows.append((roll_number, name, *marks, average))
            seen_roll_numbers.add(roll_number)

        existing_temporary = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (temporary_table,),
        ).fetchone()
        if existing_temporary:
            raise StorageError(
                f"Cannot safely upgrade the database because {temporary_table} already exists."
            )

        connection.execute(_students_schema(temporary_table))
        connection.executemany(
            f"INSERT INTO {temporary_table} VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            normalized_rows,
        )
        connection.execute("DROP TABLE students")
        connection.execute(f"ALTER TABLE {temporary_table} RENAME TO students")
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        connection.commit()
    except StorageError as exc:
        connection.rollback()
        # Keep the original table open and usable when only historical records
        # violate current input rules. The UI can then let the user correct them.
        if str(exc).startswith("Cannot safely upgrade student record"):
            return
        raise
    except (ValueError, sqlite3.DatabaseError) as exc:
        connection.rollback()
        raise StorageError(
            "The existing student database could not be upgraded safely. "
            "The schema change was rolled back; back up and inspect the database before retrying. "
            f"Details: {exc}"
        ) from exc

def _migrate_legacy_database(source_path: Path, target_path: Path) -> None:
    """Copy a legacy database via SQLite backup into a temp file, then atomically publish it."""
    source = source_path.expanduser().resolve()
    target = target_path.expanduser().resolve()
    if source == target:
        return

    temporary_path: Path | None = None
    source_connection: sqlite3.Connection | None = None
    target_connection: sqlite3.Connection | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=target.name + ".migration-",
            suffix=".tmp",
            dir=target.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)

        source_uri = source.as_uri() + "?mode=ro"
        source_connection = sqlite3.connect(source_uri, uri=True)
        _validate_legacy_schema(source_connection, source)
        source_integrity = source_connection.execute("PRAGMA integrity_check").fetchone()
        if not source_integrity or source_integrity[0] != "ok":
            raise StorageError(f"Cannot migrate {source}: SQLite integrity check failed.")

        target_connection = sqlite3.connect(str(temporary_path))
        source_connection.backup(target_connection)
        target_connection.commit()
        target_integrity = target_connection.execute("PRAGMA integrity_check").fetchone()
        if not target_integrity or target_integrity[0] != "ok":
            raise StorageError("The migrated database failed its integrity check.")

        target_connection.close()
        target_connection = None
        source_connection.close()
        source_connection = None
        os.replace(temporary_path, target)
    except StorageError:
        raise
    except (OSError, sqlite3.DatabaseError) as exc:
        raise StorageError(
            f"Could not safely migrate the existing database at {source_path}: {exc}"
        ) from exc
    finally:
        if target_connection is not None:
            target_connection.close()
        if source_connection is not None:
            source_connection.close()
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def connect_database(
    database_path: str | Path | None = None,
    *,
    legacy_path: str | Path | None = None,
) -> sqlite3.Connection:
    """Open the app database and migrate a legacy working-directory database once.

    When no explicit database path is supplied, an existing legacy database is
    sought first in the current working directory and then beside this module.
    An explicit database path only considers an explicitly provided legacy path.
    Existing destination data is never overwritten by migration.
    """
    explicit_target = database_path is not None
    target = Path(database_path).expanduser() if explicit_target else get_database_path()
    target.parent.mkdir(parents=True, exist_ok=True)

    if not target.exists():
        if legacy_path is not None:
            candidates = [Path(legacy_path).expanduser()]
        elif not explicit_target:
            candidates = [
                Path.cwd() / DATABASE_FILENAME,
                Path(__file__).resolve().parent / DATABASE_FILENAME,
            ]
        else:
            candidates = []

        source = next(
            (
                candidate for candidate in candidates
                if candidate.is_file() and candidate.resolve() != target.resolve()
            ),
            None,
        )
        if source is not None:
            _migrate_legacy_database(source, target)

    try:
        connection = sqlite3.connect(str(target))
        _upgrade_schema(connection)
        return connection
    except StorageError:
        if "connection" in locals():
            connection.close()
        raise
    except (OSError, sqlite3.DatabaseError) as exc:
        if "connection" in locals():
            connection.close()
        raise StorageError(f"Could not open student database at {target}: {exc}") from exc

def get_database_schema_version(connection: sqlite3.Connection) -> int:
    """Return the application schema marker for startup warnings and diagnostics."""
    return int(connection.execute("PRAGMA user_version").fetchone()[0])


def insert_student_records(
    connection: sqlite3.Connection,
    records: list[tuple[object, ...]],
) -> int:
    """Validate and atomically insert a batch of student records.

    Every input record is validated and its average recomputed before the
    transaction starts. A duplicate key or database constraint failure rolls
    the entire batch back through SQLite's connection context manager.
    """
    prepared_rows = []
    seen_roll_numbers: set[str] = set()
    for row_number, record in enumerate(records, start=1):
        if len(record) != 8:
            raise ValueError(f"Record {row_number} must contain exactly eight fields.")
        try:
            roll_number, name = validate_student_identity(record[0], record[1])
            if roll_number in seen_roll_numbers:
                raise ValueError(f"Record {row_number} repeats roll number {roll_number!r}.")
            marks = parse_marks(record[2:7])
        except ValueError as exc:
            raise ValueError(f"Invalid student record {row_number}: {exc}") from exc
        prepared_rows.append(
            (roll_number, name, *marks, calculate_average(marks))
        )
        seen_roll_numbers.add(roll_number)

    if not prepared_rows:
        return 0

    with connection:
        connection.executemany(
            "INSERT INTO students "
            "(roll_number, name, marks_subject1, marks_subject2, marks_subject3, "
            "marks_subject4, marks_subject5, average_marks) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            prepared_rows,
        )
    return len(prepared_rows)

