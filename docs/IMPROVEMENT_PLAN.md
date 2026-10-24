# Repository Audit and Improvement Plan

Last audited: 2026-10-25
Audit branch: `work/student-management-hardening-2026-10-25`
Default branch: `main` (kept unchanged)

## Repository inventory

- `Student.py`: current Tkinter + SQLite entry point; CRUD, grade/report actions, and file import/export.
- `Student Management System.py`: separate terminal implementation using an in-memory dictionary and a text export.
- `Student Management System Final.py`: older minimal Tkinter implementation sharing the SQLite filename/schema.
- `student_core.py`: UI-independent mark validation, average calculation, and grade rules.
- `tests/test_student_core.py`: unit coverage for the shared mark rules.
- `.github/workflows/python-checks.yml`: Python syntax compilation and unit tests.
- `README.md`, `.gitignore`: setup, scope, and local-file ignore rules.
- `Student_Management_System [ Final Edited ].docx`: project report artifact.
- `students_database.db`: tracked SQLite database with the `students` table; its contents must be treated as potentially sensitive.
- `IMG-20240801-WA0031.jpg` through `IMG-20240801-WA0053.jpg`: 23 screenshots documenting the old terminal application, sample records, and report output. They are not referenced by the current README.

## Findings

### Confirmed from source

1. The terminal version's save format writes roll number, name, five marks and average as comma-separated fields, but its loader only reads the first mark as the marks list and takes the second mark as the average. Save/load therefore does not round-trip correctly.
2. The terminal version accepts unchecked marks and blank fields; repeated roll numbers overwrite existing in-memory records without warning.
3. Both older variants duplicate business rules, so validation and grade logic can drift.
4. The current Tkinter view concatenates every student into one label rather than showing a scrollable table. The twelve actions are packed onto one horizontal row, making the layout fragile on normal screen widths.
5. Search and detail actions only show message boxes; they do not load the selected record into the editable fields. Updates require manually re-entering every field.
6. The UI and database connection are created at module import time, which blocks straightforward headless tests of persistence and UI actions.
7. The SQLite table has no database-level `NOT NULL` or score-range constraints; application validation alone cannot protect against legacy or external writes.
8. The desktop app uses a relative database path. Running it from a different working directory can silently create/use a different database.
9. `.gitignore` now ignores the database filename, but that does not untrack the database already committed. Repository history is not scrubbed by this rule.
10. The current CI validates syntax and shared-core tests only; it does not exercise database transactions, CSV compatibility, or GUI interaction.
11. The screenshot set is mostly code/output evidence for the terminal version and is not linked from project documentation. Sample outputs should be reviewed for consistency with current behavior.
12. The Word report is present as a binary artifact. The GitHub content connector exposes text source files and base64 for binary files, but does not provide extracted DOCX text; its prose has therefore not been independently compared line-by-line with the implementation in this pass.

## Ordered work plan

Each task is intended to be completed and validated before progressing. Keep changes on a feature branch and leave `main` untouched until reviewed.

| ID | Priority | Task | Completion criteria | Status |
| --- | --- | --- | --- | --- |
| A0 | P0 | Establish a written audit inventory and prioritized plan | Inventory, confirmed defects, acceptance criteria and scope are recorded | Done |
| A1 | P1 | Repair terminal save/load round-tripping | CSV round-trips all five marks, names with commas, and average recomputation; malformed imports fail without partial mutation; automated regression tests pass | Done |
| A2 | P1 | Complete core validation across all entry points | Both CLI and GUI reject invalid/missing marks and identifiers without crashing; shared grading logic is used consistently | In progress |
| A3 | P1 | Make persistence safe and testable | Explicit application-data path, safe one-time migration behavior, clear error paths, and tests using temporary databases; no silent data loss | Planned |
| A4 | P1 | Resolve tracked database/privacy exposure | Decide whether the tracked database is genuine demo data; remove/sanitize it from the delivered tree only with a data-preserving migration plan; document that history needs separate cleanup | Planned |
| A5 | P2 | Improve desktop CRUD workflow | Scrollable table, responsive button layout, selecting a row populates fields, clear success/error feedback, and delete confirmation | Planned |
| A6 | P2 | Enforce persistence integrity | Schema constraints or migration, consistent average recomputation, transaction tests, and regression handling for duplicate roll numbers | Planned |
| A7 | P2 | Strengthen automated tests and CI | Regression tests for CSV compatibility, SQLite transactions, schema initialization, and pure domain logic; tests run on supported Python versions | Planned |
| A8 | P3 | Clarify legacy entry points and project report | State one supported entry point, label/archive historical variants, reconcile report with code, document screenshots and their sample-data status | Planned |
| A9 | P3 | Documentation and release hygiene | Setup instructions verified on Windows/Linux, known limitations stated accurately, no generated data or private records committed | Planned |

## Working rules

- Do not rewrite or delete user records without a backup/migration path.
- Do not claim the project is production-ready; it currently lacks authentication, authorization, and audit logging.
- Do not weaken tests to make a change pass.
- Keep each task in a focused commit and run the relevant checks before starting the next task.
- A successful syntax/unit workflow does not substitute for GUI/manual testing.
