"""Unit tests for student marks validation and grade calculation."""

import unittest

from student_core import calculate_average, grade_for_average, parse_marks, validate_student_identity


class ParseMarksTests(unittest.TestCase):
    def test_accepts_five_valid_marks_and_numeric_strings(self):
        self.assertEqual(parse_marks(["0", "25", "50.5", 75, 100]), [0.0, 25.0, 50.5, 75.0, 100.0])

    def test_rejects_wrong_number_of_marks(self):
        with self.assertRaisesRegex(ValueError, "all 5 subjects"):
            parse_marks([10, 20, 30, 40])

    def test_rejects_blank_and_non_numeric_marks(self):
        for values in (["10", "20", "", "40", "50"], [10, 20, "oops", 40, 50]):
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    parse_marks(values)

    def test_rejects_marks_outside_the_allowed_range(self):
        for mark in (-0.01, 100.01):
            with self.subTest(mark=mark):
                with self.assertRaisesRegex(ValueError, "between 0 and 100"):
                    parse_marks([mark, 20, 30, 40, 50])

    def test_rejects_nan_and_infinity(self):
        for mark in ("nan", "inf", "-inf"):
            with self.subTest(mark=mark):
                with self.assertRaisesRegex(ValueError, "finite"):
                    parse_marks([mark, 20, 30, 40, 50])


class AverageAndGradeTests(unittest.TestCase):
    def test_calculates_arithmetic_average(self):
        self.assertEqual(calculate_average([50, 60, 70, 80, 90]), 70.0)

    def test_grade_boundaries(self):
        cases = [(100, "A"), (90, "A"), (89.99, "B"), (80, "B"),
                 (79.99, "C"), (70, "C"), (69.99, "D"), (60, "D"),
                 (59.99, "F"), (0, "F")]
        for average, expected in cases:
            with self.subTest(average=average):
                self.assertEqual(grade_for_average(average), expected)

    def test_rejects_invalid_average(self):
        for average in (-1, 101, float("nan"), float("inf")):
            with self.subTest(average=average):
                with self.assertRaises(ValueError):
                    grade_for_average(average)


class StudentIdentityTests(unittest.TestCase):
    def test_trims_required_identity_fields(self):
        self.assertEqual(validate_student_identity("  S-10  ", "  Sam Student  "), ("S-10", "Sam Student"))

    def test_rejects_blank_roll_number_or_name(self):
        for roll, name in (("", "Name"), ("  ", "Name"), ("S-11", ""), ("S-11", "  ")):
            with self.subTest(roll=roll, name=name):
                with self.assertRaises(ValueError):
                    validate_student_identity(roll, name)


if __name__ == "__main__":
    unittest.main()
