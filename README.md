# Student Management System

A small Python student-record application with a Tkinter desktop interface and SQLite persistence.

## Current application

- **`Student.py`** — desktop UI with create, search, update, delete, listing, grade, report-card, and text-file import/export actions.
- **`student_data_io.py`** — shared CSV import/export logic, including compatibility with legacy unquoted names and average recomputation.
- **`Student Management System.py`** — older terminal-menu version that keeps its data in memory until saved.
- **`Student Management System Final.py`** — earlier minimal Tkinter variant.
- **`Student_Management_System [ Final Edited ].docx`** — project report/documentation artifact.
- **`students_database.db`** — a database file currently tracked in this repository. Treat its contents as potentially sensitive; do not use this repository to distribute real student records.

The variants are preserved for reference. The maintained starting point for development is `Student.py`.

## Requirements

- Python 3.10 or newer is recommended.
- Tkinter (often included with Python; on some Linux distributions it must be installed separately).
- SQLite support, included with standard Python builds.

There are no third-party runtime dependencies.

## Run

From the repository directory:

```bash
python Student.py
```

The app opens a desktop window and creates/uses `students_database.db` relative to the process's current working directory. Run it from the repository directory if you intend to use the bundled database. Back up the database before testing imports, edits, or deletion.

For a Linux desktop session, ensure Tkinter is installed and a display server is available. A headless shell or server cannot show a Tkinter window.

## Tests

CSV import validates all rows before writing, rejects malformed or duplicate roll numbers in a file, and recalculates averages from the five subject marks. The older terminal export's unquoted CSV rows are supported where their trailing marks/average fields make the record unambiguous.

Run the validation and grading unit tests:

```bash
python -m unittest discover -s tests -v
```

Check Python syntax across the project:

```bash
python -m compileall -q .
```

## Data and privacy

Student names, roll numbers, and marks are educational records. Use synthetic data for demos and tests. Do not commit real records, exports, credentials, or personal information. The database is already tracked in the current repository history; adding it to `.gitignore` does not remove it from Git history. Before making this project public or continuing to use it with real data, inspect and sanitize the tracked database and consider moving persistent data to a private per-user application-data directory.

## Known scope

This is a local desktop project, not a multi-user web service. It does not currently provide authentication, role-based authorization, audit logs, or secure remote access. Do not treat it as a production school information system without a separate security, privacy, backup, and data-integrity review.
