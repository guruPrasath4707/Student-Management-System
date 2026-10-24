# Repository Audit and Improvement Plan

Last audited: 2026-10-25  
Default branch: `main`  
Working branch: `work/student-management-hardening-2026-10-25`  
Current review: [PR #2](https://github.com/guruPrasath4707/Student-Management-System/pull/2)

## Repository inventory

The working branch contains the maintained desktop program, two historical application variants, shared domain/data/storage modules, four test files, a GitHub Actions workflow, source documentation, the historic Word report, a tracked SQLite database, and 23 historic JPEG screenshots. The working tree was checked through the GitHub tree and individual file contents; the binary document and assets were audited through an isolated CI extraction/audit run.

| Path | Purpose and current disposition |
| --- | --- |
| `Student.py` | Maintained Tkinter + SQLite desktop app; record CRUD, grades/reports, CSV exchange, scrollable table |
| `Student Management System.py` | Legacy terminal menu using an in-memory dictionary and CSV file; its active data is separate from desktop SQLite |
| `Student Management System Final.py` | Minimal historical Tkinter variant, retained for reference |
| `student_core.py` | Shared identity/marks validation, averages, grade rules |
| `student_data_io.py` | CSV parsing/serialization and supported legacy row compatibility |
| `student_storage.py` | Per-user database location, safe migration, schema validation/upgrade, constraints and atomic batch insert |
| `tests/test_student_core.py` | Domain and identity validation tests |
| `tests/test_student_data_io.py` | CSV round-trip, legacy compatibility and malformed-input tests |
| `tests/test_student_storage.py` | Data paths, migration, schema constraints and transaction tests |
| `tests/test_cli_validation.py` | Black-box terminal input and import-conflict regression tests |
| `.github/workflows/python-checks.yml` | Compile and unit-test workflow; now configured for Python 3.10/3.12/3.13 on Ubuntu and Windows |
| `README.md` | Setup, limits, data location and privacy warnings |
| `docs/PROJECT_REPORT.md` | Code-aligned technical report for the actual maintained implementation |
| `Student_Management_System [ Final Edited ].docx` | Historic incomplete report artifact; contains identifying details; preserved pending approval |
| `students_database.db` | Tracked legacy database; contents need owner-approved backup/migration and privacy decision |
| `IMG-20240801-WA0031.jpg`–`IMG-20240801-WA0053.jpg` | 23 historic CLI screenshots; contain student-style identifiers, names and marks, so treat as potentially sensitive |

## Baseline defects found and resulting status

The initial source audit found incorrect legacy CLI CSV field parsing, unvalidated marks and identities, duplicate business rules, a cramped label-based desktop record view, a fragile custom-font initialization, relative-path database creation, no database-level mark/average constraints, weak data-import tests, and misleading/incomplete legacy project documentation.

The active branch now corrects the CLI CSV round-trip; shares validation and grade rules; protects in-memory records from import collisions; validates all imported rows before mutation; uses a per-user SQLite path; migrates legacy data without deleting its source; uses schema constraints; commits batch imports atomically; provides a scrollable desktop table and delete confirmation; and contains a technical report that describes the implemented system rather than copying unverified claims into the historic Word document.

## Privacy audit: findings that remain unresolved

The committed database passed SQLite's integrity check and contains two student rows. Neither name matched the simple generic-placeholder patterns used for the audit; no blank identities were detected. One row has an out-of-range subject mark, and one row has a stale or invalid average. Placeholder-name matching is only a heuristic and cannot establish that the records are synthetic. The 23 screenshots also show student-style record data, and the historic DOCX contains identifying student/school details.

No record values are copied into this plan or printed to CI logs. The old DB, screenshots and DOCX have **not** been deleted, replaced or rewritten. Before any such change, back up the source artifacts, verify the migrated records, establish which material may be published, and obtain owner approval for redaction/removal. Deleting a file from the current tree does not erase older copies from Git history; history cleanup is a separate coordinated operation.

## Ordered work plan

Do not start a new task until the prior task's relevant tests/acceptance checks pass. Keep edits on the working branch; leave `main` unchanged until the pull request is reviewed.

| ID | Priority | Task | Completion criteria | Status |
| --- | --- | --- | --- | --- |
| A0 | P0 | Establish full inventory and ordered plan | Repository files inventoried; initial defects and acceptance criteria recorded | Done |
| A1 | P1 | Repair legacy CLI CSV save/load | Correct five-mark round-trip, comma-containing names, average recomputation, malformed-file rejection and no partial in-memory mutation | Done |
| A2 | P1 | Apply shared validation across active entry points | Missing identifiers/names and invalid marks fail safely; average/grade rules are shared | Done; domain and CLI regression tests pass across Windows and Linux on Python 3.10, 3.12 and 3.13 |
| A3 | P1 | Make desktop persistence safe and testable | Per-user path, source-preserving migration, database constraints, schema-version validation and isolated storage tests | Done |
| A4 | P1 | Resolve tracked DB and historic-data privacy exposure | Preserve a verified backup; confirm data ownership/meaning; obtain approval; sanitize/remove only with migration plan; decide separately on history cleanup | Deferred: source contains two non-generic-looking records and invalid historical data; no destructive change made |
| A5 | P2 | Improve desktop CRUD flow | Scrollable table, row-to-form selection, responsive actions and deletion confirmation | Implemented; a stable row identifier now lets the form repair/delete legacy records with blank roll numbers; automated Windows tests cover startup and repair/reopen. Manual visual review still required |
| A6 | P2 | Enforce database integrity | Constraints on identity/marks/derived average; schema upgrade and whole-batch rollback verified by tests | Done; legacy-invalid records remain accessible, are flagged for review, and are upgraded after correction/restart; migration and rollback tests pass |
| A7 | P2 | Regression testing and CI | Domain, CSV, storage/migration and CLI tests; matrix on supported Python versions | Done; all 46 tests and the six-job Ubuntu/Windows × Python 3.10/3.12/3.13 matrix passed on head `5c572ed` (run [40131300654](https://github.com/guruPrasath4707/Student-Management-System/actions/runs/40131300654)) |
| A8 | P3 | Replace inaccurate/incomplete technical documentation | Accurate architecture, schema, grading, persistence, CSV and security limits documented; historic DOCX preserved and flagged | Done for new Markdown report; historic DOCX must not be redistributed without approved redaction |
| A9 | P3 | Release hygiene and portability | CI on Windows/Linux, precise setup docs, no new data artifacts in commits, clean CI results, GUI smoke test documented | In progress; automated Windows startup and legacy-repair smoke tests are in place; manual visual/interaction review and owner-gated privacy remediation remain |
| A10 | P3 | Improve workflow features without overclaiming | Add configurable subjects/terms, dedicated report export and better record filtering only after usability requirements are defined and tests are planned | Planned |

## Working rules

- Never overwrite or delete student data as a shortcut; make and verify backups before migration or redaction.
- Do not copy names, roll numbers, or marks from historic assets into docs, test fixtures, commit messages or CI logs.
- Do not describe this local single-user app as production-ready; it lacks authentication, authorization, audit history and multi-user controls.
- Do not weaken tests to make code pass.
- A green syntax/unit workflow is not a substitute for visually testing Tkinter on a real desktop.
- Update this plan after each completed task and use the latest branch head when making edits.
