# Student Management System — Technical Project Report

**Document status:** Repository-aligned technical report  
**Project type:** Local Python desktop application with a legacy command-line variant  
**Prepared from:** Source files, automated tests, and repository CI  
**Last reviewed:** 25 October 2026

## 1. Executive summary

The Student Management System stores student identifiers and marks for five subjects. The maintained desktop application uses Python's Tkinter GUI toolkit and SQLite. It supports adding, viewing, searching, updating, removing and sorting records; calculating averages and letter grades; generating report-card summaries; and importing or exporting records.

The repository also contains an older command-line implementation. That version holds active records in memory and uses CSV-formatted text files for persistence. It is a legacy variant, not a second interface to the SQLite database.

This is a small, single-user learning project. It is not a production student information system and does not implement user authentication, role-based access, audit logging or multi-user concurrency workflows.

## 2. Problem statement and objectives

Manual tracking of student identifiers and marks across five subjects can make routine operations repetitive and error-prone. This project demonstrates how a local program can centralize records and automate basic calculations.

The implemented objectives are to:
- keep each student's roll number, name and subject marks together;
- calculate an arithmetic mean from five subject marks;
- apply the existing A–F grading thresholds consistently;
- support common record-management operations;
- persist desktop records with SQLite;
- exchange records through CSV; and
- validate inputs and test data handling.

## 3. Scope and assumptions

Each record contains a roll number, a student name, five marks, and a derived average. Marks are expected to be finite numeric values in the inclusive range 0–100.

The application uses a single local database. It does not model classes, academic terms, individual subject names, attendance, fees, guardians, teachers, permissions or institutional reporting. The five subject columns are generic fields rather than a configurable subject catalogue.

The letter grade is a simple project rule. It is not a claim that these thresholds match every institution's grading policy.

## 4. Technology and requirements

| Component | Purpose |
| --- | --- |
| Python 3.10 or newer | Application and validation logic |
| Tkinter / ttk | Native desktop user interface |
| SQLite (sqlite3) | Local desktop persistence |
| Python csv module | Correctly quoted CSV input and output |
| unittest | Automated regression tests |
| GitHub Actions | Syntax compilation and automated tests |

No third-party Python runtime packages are required. Tkinter is commonly included with Python but may need to be installed separately on some Linux distributions. A graphical display is needed to launch either Tkinter program.

## 5. Repository layout

| File or directory | Role |
| --- | --- |
| Student.py | Maintained Tkinter + SQLite application |
| student_core.py | UI-independent mark, average, grade and identity validation |
| student_data_io.py | CSV serialization and backward-compatible import parsing |
| student_storage.py | Per-user database path, legacy migration, schema upgrade and transactional batch insert |
| Student Management System.py | Legacy terminal implementation using an in-memory dictionary |
| Student Management System Final.py | Earlier minimal Tkinter implementation retained for reference |
| tests/ | Unit, persistence and CLI regression tests |
| .github/workflows/python-checks.yml | Python version-matrix CI |
| docs/IMPROVEMENT_PLAN.md | Audit findings, priorities and task status |
| Student_Management_System [ Final Edited ].docx | Historical report artifact; see privacy warning in README |
| IMG-20240801-WA0031.jpg to IMG-20240801-WA0053.jpg | Historical terminal screenshots, not runtime assets |

## 6. Application architecture

The maintained desktop app separates three responsibilities.

1. **Presentation:** Student.py builds the Tkinter form, action grid and scrollable table. Selecting a row loads its values into the form.
2. **Domain rules:** student_core.py validates identity and marks, computes the arithmetic average, and maps averages to grades. These rules can be tested without opening a GUI.
3. **Data handling:** student_data_io.py reads and writes the eight-field record format. student_storage.py selects the data directory, upgrades the original SQLite table, applies database constraints and inserts batches transactionally.

The CLI uses the shared domain and CSV functions but intentionally keeps active records in memory. Changes made in the CLI do not automatically update the desktop app's SQLite database.

## 7. Data model

The desktop database uses one students table.

| Field | Meaning | Validation |
| --- | --- | --- |
| roll_number | Student identifier | Required, unique, nonblank |
| name | Student display name | Required, nonblank |
| marks_subject1 through marks_subject5 | Five subject marks | Required, numeric, 0–100 |
| average_marks | Arithmetic mean of the five marks | Derived value; database constraint checks consistency |

The database schema upgrade preserves valid legacy rows, normalizes whitespace around identifiers and names, recalculates averages from subject marks, and adds required-field, range and mean-consistency constraints. It refuses to silently drop rows that have invalid historical marks or conflicting identifiers.

## 8. Calculations and grading

The average is calculated as:

**average = (subject 1 + subject 2 + subject 3 + subject 4 + subject 5) / 5**

The repository's grading scale is:

| Average | Grade |
| --- | --- |
| 90–100 | A |
| 80–under 90 | B |
| 70–under 80 | C |
| 60–under 70 | D |
| 0–under 60 | F |

Blanks, non-numeric values, NaN, infinity and marks below 0 or above 100 are rejected. Imported averages are recomputed from marks rather than trusted from a file.

## 9. CSV exchange

New exports use Python's CSV writer, so names containing commas are quoted correctly. The importer also supports the legacy unquoted format when the trailing five mark fields and average make the row shape unambiguous.

Every row is validated before the parsed batch is returned. The SQLite import helper validates the batch again and inserts it in a transaction. If a database constraint or duplicate roll number causes insertion to fail, the entire batch rolls back. The current user-facing export filename still ends in .txt for backward compatibility even though the file contents are CSV-formatted.

The CLI import validates the whole file before changing the in-memory dictionary. The CLI and desktop app do not share a live store: the CLI dictionary and desktop SQLite database are separate data locations.

## 10. Persistence and migration

The desktop application stores data in the per-user application-data directory:

- **Windows:** %APPDATA%/StudentManagementSystem/
- **macOS:** ~/Library/Application Support/StudentManagementSystem/
- **Linux:** $XDG_DATA_HOME/StudentManagementSystem/, or ~/.local/share/StudentManagementSystem/ when XDG_DATA_HOME is unset.

Set STUDENT_MANAGEMENT_DATA_DIR to override the data directory. When the destination does not exist, the storage module can copy a legacy students_database.db from the current working directory or beside the application using SQLite's backup API. Migration validates source integrity, leaves the source untouched, and does not overwrite an existing destination.

A legacy-schema upgrade runs transactionally. Invalid historical rows cause a clear storage error and remain available for manual correction; they are not automatically discarded. Back up the database before running the application against valuable records.

## 11. User interface

The maintained desktop screen includes a student details form, a responsive action-button grid and a scrollable table showing identifiers, names, all five subject marks and the average. The table can be sorted by average, selected rows populate the form, search focuses a matching row, and deletion requires confirmation.

Automated CI checks do not prove that the interface renders correctly on every Windows or Linux desktop. A manual visual smoke test is still required on a real desktop environment.

## 12. Tests and verification

The repository has automated tests for:
- mark parsing, range boundaries, non-finite values, averages, grades and required identity fields;
- canonical CSV round-trips, names containing commas and legacy-format import;
- malformed files and duplicate identifiers;
- OS-specific data paths;
- database initialization and legacy migration;
- integrity checks, schema upgrade, average recomputation and database-level constraints;
- transactional bulk insert, validation-before-write and rollback on duplicate keys; and
- black-box CLI validation in a temporary working directory.

GitHub Actions compiles Python sources and runs the tests on Python 3.10, 3.12 and 3.13. The workflow is configured to exercise both Ubuntu and Windows runners; each six-job matrix must pass before a release is considered validated. See the [repository Actions runs](https://github.com/guruPrasath4707/Student-Management-System/actions).

## 13. Privacy and security limitations

This application must not be used to distribute real student records in a public repository. Student identifiers, names and marks are educational records; use synthetic examples for demos and tests. The repository currently has a tracked SQLite database and historical report/screenshots that require an explicit privacy review. Removing a file from the current tree does not erase past copies from Git history.

The application has no authentication, role-based access, audit log, encryption-at-rest layer, remote-access controls or multi-user transaction coordination. It should not be represented as a production school information system. Database backups, access controls, retention requirements, privacy obligations and recovery procedures must be designed before any real institutional use.

## 14. Known limitations and future work

1. Resolve the tracked SQLite database and historical-asset privacy concern only after a verified backup, data-preserving migration plan and owner-approved redaction/removal decision. History cleanup, if needed, is separate from removing files from the current tree.
2. Add configurable subject names and academic terms instead of assuming five generic subjects for every school or term.
3. Add structured filtering and a dedicated report-card export flow; report cards are currently presented as summaries rather than a fully formatted export artifact.
4. Perform a visual smoke test on a Windows desktop and test migration with a verified copy of the historic database. Automated GUI rendering has not been established by the current headless test suite.
5. Consider separating Tkinter construction from application logic so UI/controller interactions can be tested without creating a window at module import time.
6. Do not reuse the historic Word report or screenshots in a public report/presentation until the owner has confirmed the intended academic context and approved redaction of identifying content.
7. If the project grows beyond a local learning tool, perform a separate privacy/security architecture review before adding multi-user or remote access.

The legacy CLI import policy is now explicit: if an imported batch contains a roll number already present in the in-memory store, the entire import is rejected and no existing record is overwritten.

## 15. Conclusion

The project demonstrates a basic Python student-record workflow with a desktop interface, SQLite storage, CSV exchange and automated validation. The maintenance work focuses on record integrity, compatibility and testability while preserving old entry points. The remaining report and database privacy review, manual GUI validation and production-scope limitations must be addressed before broader distribution or real-record use.
