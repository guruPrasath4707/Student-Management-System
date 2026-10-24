"""Regression tests for CSV compatibility and student record validation."""

import unittest

from student_data_io import parse_student_csv_text, serialize_student_rows


class StudentCsvTests(unittest.TestCase):
    def test_round_trip_quotes_commas_and_recomputes_average(self):
        text = serialize_student_rows([
            ("S-01", "Rao, Ananya", 10, 20, 30, 40, 50, 999),
        ])
        rows = parse_student_csv_text(text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][:2], ("S-01", "Rao, Ananya"))
        self.assertEqual(rows[0][2:7], (10.0, 20.0, 30.0, 40.0, 50.0))
        self.assertEqual(rows[0][7], 30.0)

    def test_reads_legacy_unquoted_name_containing_comma(self):
        rows = parse_student_csv_text("S-02,Ananya,Rao,10,20,30,40,50,30\n")
        self.assertEqual(rows[0][:2], ("S-02", "Ananya,Rao"))
        self.assertEqual(rows[0][2:7], (10.0, 20.0, 30.0, 40.0, 50.0))
        self.assertEqual(rows[0][7], 30.0)

    def test_reads_old_format_and_recomputes_stale_average(self):
        rows = parse_student_csv_text("S-03,Test Student,10,20,30,40,50,99\n")
        self.assertEqual(rows[0][7], 30.0)

    def test_rejects_malformed_rows(self):
        with self.assertRaisesRegex(ValueError, "Line 1"):
            parse_student_csv_text("S-04,Incomplete,10,20\n")

    def test_rejects_duplicate_roll_numbers_without_returning_partial_data(self):
        with self.assertRaisesRegex(ValueError, "repeats roll number"):
            parse_student_csv_text(
                "S-05,First,10,20,30,40,50,30\n"
                "S-05,Second,20,30,40,50,60,40\n"
            )

    def test_rejects_invalid_marks_and_stored_averages(self):
        for text in (
            "S-06,Out of range,10,20,30,40,101,40\n",
            "S-07,Invalid average,10,20,30,40,50,nan\n",
        ):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_student_csv_text(text)

    def test_rejects_incomplete_export_record(self):
        with self.assertRaisesRegex(ValueError, "eight fields"):
            serialize_student_rows([("S-08", "Short", 10, 20)])

if __name__ == "__main__":
    unittest.main()
