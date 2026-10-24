"""Validated, UI-independent rules for student marks and grades."""

from __future__ import annotations

import math
from collections.abc import Iterable

SUBJECT_COUNT = 5
MIN_MARK = 0.0
MAX_MARK = 100.0


def parse_marks(values: Iterable[str | int | float]) -> list[float]:
    """Convert exactly five marks to finite numbers in the inclusive 0–100 range.

    Raises:
        ValueError: If the number of marks or any mark is invalid.
    """
    raw_values = list(values)
    if len(raw_values) != SUBJECT_COUNT:
        raise ValueError(f"Enter marks for all {SUBJECT_COUNT} subjects.")

    marks: list[float] = []
    for index, raw in enumerate(raw_values, start=1):
        value = str(raw).strip()
        if not value:
            raise ValueError(f"Enter a mark for Subject {index}.")
        try:
            mark = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Subject {index} must be a number.") from exc
        if not math.isfinite(mark):
            raise ValueError(f"Subject {index} must be a finite number.")
        if not MIN_MARK <= mark <= MAX_MARK:
            raise ValueError(f"Subject {index} must be between 0 and 100.")
        marks.append(mark)
    return marks


def calculate_average(marks: Iterable[str | int | float]) -> float:
    """Return the arithmetic mean of five validated subject marks."""
    validated = parse_marks(marks)
    return sum(validated) / SUBJECT_COUNT


def grade_for_average(average: float) -> str:
    """Map an average mark to the project's existing A–F grading scale."""
    try:
        score = float(average)
    except (TypeError, ValueError) as exc:
        raise ValueError("Average must be a number.") from exc
    if not math.isfinite(score) or not MIN_MARK <= score <= MAX_MARK:
        raise ValueError("Average must be between 0 and 100.")
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"

def validate_student_identity(roll_number: str, name: str) -> tuple[str, str]:
    """Normalize and validate the two required student identity fields."""
    normalized_roll = str(roll_number).strip()
    normalized_name = str(name).strip()
    if not normalized_roll:
        raise ValueError("Roll number is required.")
    if not normalized_name:
        raise ValueError("Student name is required.")
    return normalized_roll, normalized_name

