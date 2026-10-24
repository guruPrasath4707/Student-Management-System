# Student Management System

A small Python student-record application with a Tkinter desktop interface and SQLite persistence.

## Current application

- **`Student.py`** — maintained desktop UI with create, search, update, delete, listing, grade, report-card, and CSV import/export actions. It uses a scrollable student table; selecting a row loads the record into the form.
- **`student_data_io.py`** — shared CSV import/export logic, including compatibility with legacy unquoted names and average recomputation.
- **`Student Management System.py`** — older terminal-menu version that keeps its data in memory until saved.
- **`Student Management System Final.py`** — earlier minimal Tkinter variant.
- **`docs/PROJECT_REPORT.md`** — current code-aligned technical report.
- **`docs/IMPROVEMENT_PLAN.md`** — ordered audit roadmap, task acceptance criteria, and status.
- **`Student_Management_System [ Final Edited ].docx`** — historical report artifact; incomplete and contains identifying information. Do not reuse until its owner approves redaction.
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

The app stores its database in the current user's application-data directory instead of writing persistent records into the source checkout. On Windows it uses `%APPDATA%/StudentManagementSystem/`, on macOS `~/Library/Application Support/StudentManagementSystem/`, and on Linux `$XDG_DATA_HOME/StudentManagementSystem/` (or `~/.local/share/StudentManagementSystem/` if `XDG_DATA_HOME` is unset). Set `STUDENT_MANAGEMENT_DATA_DIR` to override the data directory. On first launch, if the destination database does not already exist, the app attempts a one-time SQLite backup migration from a legacy `students_database.db` in the working directory or beside the application. Migration leaves the source file unchanged and refuses to overwrite an existing destination. If historic records violate current validation rules, the desktop app keeps the original table available, highlights records that need review, and warns at startup instead of deleting records or blocking access. Correct the highlighted name/marks, close the app, and reopen it to complete the constrained-schema upgrade. Back up records before testing imports, edits, or deletion.

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

For the tracked database, legacy report, and historical screenshots, see [`docs/PRIVACY_REMEDIATION.md`](docs/PRIVACY_REMEDIATION.md) for the owner-approved backup, migration, removal, and optional history-cleanup sequence.

## Project report status

The root-level Word report is a legacy artifact, not complete project documentation. Its extracted text contains front matter and a table of contents but no substantive chapter content matching the listed sections. It also contains identifying student/school details and inconsistent academic-year labels. Do not reuse or redistribute it until its owner has reviewed and approved redaction. The new technical report in docs/PROJECT_REPORT.md describes the current code without repeating those personal details. The original Word file remains untouched pending an owner-approved decision.

## Historical screenshots

The root directory contains 23 image files named `IMG-20240801-WA0031.jpg` through `IMG-20240801-WA0053.jpg`. They document the earlier terminal implementation and example inputs/outputs, not screenshots of the maintained Tkinter interface. They are not loaded by the application. Review these historical images for sample-record privacy and consistency before reusing them in a public report or presentation.
