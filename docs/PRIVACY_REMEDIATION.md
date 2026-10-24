# Privacy Remediation Checklist

**Status:** Owner review required; source artifacts intentionally preserved  
**Last audit:** 25 October 2026

## Findings (no record values reproduced)

- The public repository currently tracks `students_database.db`. A read-only audit found two records that do not look like generic placeholders; at least one subject mark is outside the accepted range, and stored average data is inconsistent. Do not treat the database as safe synthetic demo data without the owner's verification.
- The historical root-level Word report contains identifying student/school information, inconsistent academic-year labels, and little substantive report text. It should not be redistributed as-is.
- The 23 historical screenshots contain examples of the old CLI and sample record/output flows. Review every image before republishing them; file names and code-only screenshots do not establish that their contents are safe.

This document deliberately excludes names, roll numbers, marks and the report's personal details.

## Safe remediation sequence

### 1. Preserve the original material off-repository

- Make a local backup of the database, legacy report and image assets in a trusted location outside the Git checkout.
- Record cryptographic hashes for the archived files and restrict access to the backup. Do not commit or upload the backup into another public repository.
- Verify that the owner can open the backup and that the number of records matches expectations before making repository changes.

### 2. Verify the local-data migration

- Use the maintained `Student.py` application with a private per-user data directory. The storage module copies the legacy SQLite file without changing the source and refuses to overwrite an existing destination.
- If invalid legacy marks are found, the app leaves the old table accessible, highlights records requiring review and displays a warning. Correct the affected record(s), close the app and reopen it; the constrained-schema upgrade then recomputes averages and validates the data.
- Compare record counts and key values locally against the backup. Do not print student values into CI logs or commit the repaired database.

### 3. Remove or replace sensitive artifacts only after verification

With an owner-approved backup and a validated replacement plan:

- Remove the tracked database from the public repository's current tree. The app can create a fresh empty database when no legacy file is present.
- Remove the incomplete identifying DOCX, or replace it with an owner-approved, redacted report. `docs/PROJECT_REPORT.md` is the current code-aligned technical report.
- Remove or replace screenshots that expose identifiable people, student records, or other private content. Retain only images cleared for publication.
- Keep the existing ignore rules so local database files and exports are not accidentally recommitted.

Removing these files in a new commit will not delete copies from previous commits, forks, clones or already downloaded artifacts.

### 4. Decide separately whether history rewriting is required

If the owner or applicable privacy requirements call for removing these artifacts from Git history, plan a separate history-rewrite operation (for example, using a reviewed Git history-filtering process). It may require a force-push and coordination with anyone who has cloned the repository. Do not perform that operation as part of an ordinary feature PR or without an explicit, reviewed recovery plan.

### 5. Add a release gate

Before future public releases, verify that the repository contains no real student records, personal report details, unreviewed screenshots, local database files or exported records. Use only synthetic demo data and have the maintainer review any binary assets before commit.

## Current repository policy

No database, report or screenshot file has been deleted or rewritten by this audit. The unresolved privacy action remains owner-gated because deleting or moving tracked files can affect local copies, and history rewriting is a separate potentially disruptive operation.
