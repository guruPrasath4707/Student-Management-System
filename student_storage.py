"""Safe application-data location and one-time migration for the SQLite store."""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from collections.abc import Mapping

DATABASE_FILENAME = "students_database.db"
APP_DIRECTORY_NAME = "StudentManagementSystem"
STUDENTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    roll_number TEXT PRIMARY KEY,
    name TEXT,
    marks_subject1 REAL,
    marks_subject2 REAL,
    marks_subject3 REAL,
    marks_subject4 REAL,
    marks_subject5 REAL,
    average_marks REAL
)
"""
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
    if missing:
        raise StorageError(
            f"Cannot migrate {source}: the students table is missing required columns: "
            + ", ".join(missing)
        )


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

    try:
        assert temporary_path is not None
        os.replace(temporary_path, target)
    except OSError as exc:
        raise StorageError(
            f"Could not publish migrated database to {target_path}: {exc}"
        ) from exc
    finally:
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
        connection.execute(STUDENTS_SCHEMA)
        connection.commit()
        return connection
    except (OSError, sqlite3.DatabaseError) as exc:
        if "connection" in locals():
            connection.close()
        raise StorageError(f"Could not open student database at {target}: {exc}") from exc
