"""CSV persistence helpers shared by the legacy CLI and Tkinter application."""

from __future__ import annotations

import csv
import math
from io import StringIO
from collections.abc import Iterable, Sequence

from student_core import calculate_average, parse_marks

FIELD_COUNT = 8


def parse_student_csv_text(text: str) -> list[tuple[str, str, float, float, float, float, float, float]]:
    """Parse current or legacy student CSV, validating every row before returning.

    The canonical row is roll number, name, five subject marks, and average.
    Older exports did not quote names containing commas. Those rows are
    recognized by their extra columns and reconstructed from the trailing six
    numeric fields. Stored averages are checked but recomputed from marks.
    """
    try:
        rows = list(csv.reader(StringIO(text, newline="")))
    except csv.Error as exc:
        raise ValueError(f"Invalid CSV: {exc}") from exc

    parsed: list[tuple[str, str, float, float, float, float, float, float]] = []
    seen_roll_numbers: set[str] = set()
    for line_number, row in enumerate(rows, start=1):
        if not row:
            continue
        if len(row) == FIELD_COUNT:
            roll_number, name = row[0].strip(), row[1].strip()
            mark_fields, stored_average = row[2:7], row[7]
        elif len(row) > FIELD_COUNT:
            # Legacy exports joined fields with commas without CSV quoting.
            roll_number = row[0].strip()
            name = ",".join(row[1:-6]).strip()
            mark_fields, stored_average = row[-6:-1], row[-1]
        else:
            raise ValueError(
                f"Line {line_number} must contain a roll number, name, "
                "five marks, and an average."
            )

        if not roll_number:
            raise ValueError(f"Line {line_number} is missing a roll number.")
        if not name:
            raise ValueError(f"Line {line_number} is missing a student name.")
        if roll_number in seen_roll_numbers:
            raise ValueError(f"Line {line_number} repeats roll number {roll_number!r}.")

        marks = parse_marks(mark_fields)
        try:
            prior_average = float(stored_average)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Line {line_number} has an invalid stored average.") from exc
        if not math.isfinite(prior_average) or not 0 <= prior_average <= 100:
            raise ValueError(f"Line {line_number} has an invalid stored average.")

        average = calculate_average(marks)
        parsed.append((roll_number, name, *marks, average))
        seen_roll_numbers.add(roll_number)

    return parsed


def serialize_student_rows(rows: Iterable[Sequence[object]]) -> str:
    """Serialize canonical eight-column student rows as correctly quoted CSV.

    A fresh average is calculated from the five marks so stale stored values
    cannot propagate into newly exported files.
    """
    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    seen_roll_numbers: set[str] = set()
    for line_number, row in enumerate(rows, start=1):
        if len(row) != FIELD_COUNT:
            raise ValueError(f"Record {line_number} must contain exactly eight fields.")
        roll_number, name = str(row[0]).strip(), str(row[1]).strip()
        if not roll_number:
            raise ValueError(f"Record {line_number} is missing a roll number.")
        if not name:
            raise ValueError(f"Record {line_number} is missing a student name.")
        if roll_number in seen_roll_numbers:
            raise ValueError(f"Record {line_number} repeats roll number {roll_number!r}.")
        marks = parse_marks(row[2:7])
        average = calculate_average(marks)
        writer.writerow((roll_number, name, *marks, average))
        seen_roll_numbers.add(roll_number)
    return output.getvalue()
