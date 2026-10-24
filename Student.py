import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkfont
import sqlite3

from student_core import (
    calculate_average as calculate_marks_average,
    grade_for_average,
    inspect_student_marks,
    parse_marks,
    validate_student_identity,
)
from student_data_io import parse_student_csv_text, serialize_student_rows

# Open the per-user database, migrating the old working-directory file once when present.
from student_storage import (
    StorageError,
    connect_database,
    get_database_schema_version,
    insert_student_records,
)

try:
    conn = connect_database()
except (StorageError, OSError) as exc:
    error_root = tk.Tk()
    error_root.withdraw()
    messagebox.showerror('Database Error', f"Could not open the student database: {exc}", parent=error_root)
    error_root.destroy()
    raise SystemExit(1) from exc

cursor = conn.cursor()


def add_student():
    try:
        roll_number, name = validate_student_identity(entry_roll.get(), entry_name.get())
        marks = parse_marks(entry.get() for entry in entry_marks)
    except ValueError as exc:
        messagebox.showerror('Invalid Input', str(exc))
        return

    average_marks = calculate_marks_average(marks)

    try:
        cursor.execute('''
            INSERT INTO students (roll_number, name, marks_subject1, marks_subject2, marks_subject3, marks_subject4, marks_subject5, average_marks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (roll_number, name, *marks, average_marks))
        conn.commit()
        messagebox.showinfo('Success', 'Student added successfully!')
        clear_entries()
        display_students()
    except sqlite3.IntegrityError:
        messagebox.showerror('Error', 'Student with the same roll number already exists!')

def _format_score(value):
    if value is None:
        return ""
    try:
        score = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{score:.2f}" if math.isfinite(score) else str(value)


def display_students(sort_by_average=False):
    cursor.execute(
        "SELECT roll_number, name, marks_subject1, marks_subject2, marks_subject3, "
        "marks_subject4, marks_subject5, average_marks FROM students ORDER BY roll_number"
    )
    students = cursor.fetchall()
    if sort_by_average:
        def sort_key(record):
            marks_valid, _average_stale, computed_average = inspect_student_marks(
                record[2:7], record[7]
            )
            return (not marks_valid, -(computed_average or 0.0), str(record[0] or ""))

        students.sort(key=sort_key)

    for item in student_tree.get_children():
        student_tree.delete(item)

    legacy_needs_review = get_database_schema_version(conn) < 1
    review_count = 0
    for student in students:
        roll_number, name, *scores = student
        marks_are_valid, average_is_stale, computed_average = inspect_student_marks(
            scores[:5], scores[5]
        )
        identity_is_invalid = not str(roll_number or "").strip() or not str(name or "").strip()
        needs_review = identity_is_invalid or not marks_are_valid or average_is_stale
        if legacy_needs_review and needs_review:
            review_count += 1

        displayed_average = computed_average if marks_are_valid else scores[5]
        formatted_scores = [_format_score(score) for score in scores[:5]]
        formatted_scores.append(_format_score(displayed_average))
        student_tree.insert(
            "", "end",
            values=(roll_number or "", name or "", *formatted_scores),
            tags=("legacy-invalid",) if legacy_needs_review and needs_review else (),
        )

    if "result_label" in globals():
        if legacy_needs_review:
            result_label.configure(
                text=(
                    f"Legacy database needs review: {review_count} record(s) highlighted. "
                    "Correct them, then close and reopen the app to finish the safe upgrade."
                )
            )
        else:
            result_label.configure(
                text=f"Student records: {len(students)}. Select a row to load it into the form."
            )


def clear_entries():
    entry_roll.delete(0, tk.END)
    entry_name.delete(0, tk.END)
    for entry in entry_marks:
        entry.delete(0, tk.END)


def select_student_in_table(roll_number):
    for item in student_tree.get_children():
        values = student_tree.item(item, "values")
        if values and str(values[0]).strip() == roll_number:
            student_tree.selection_set(item)
            student_tree.focus(item)
            student_tree.see(item)
            load_selected_student()
            return True
    return False


def load_selected_student(event=None):
    selected = student_tree.selection()
    if not selected:
        return
    values = student_tree.item(selected[0], "values")
    if len(values) < 8:
        return

    clear_entries()
    entry_roll.insert(0, values[0])
    entry_name.insert(0, values[1])
    for entry, mark in zip(entry_marks, values[2:7]):
        entry.insert(0, mark)


def search_student():
    roll_number = entry_roll.get().strip()
    if not roll_number:
        messagebox.showerror('Invalid Input', 'Enter a roll number to search.')
        return

    cursor.execute('SELECT * FROM students WHERE roll_number=?', (roll_number,))
    student = cursor.fetchone()

    if student:
        display_students()
        select_student_in_table(roll_number)
        messagebox.showinfo(
            'Student Found',
            f"Roll Number: {student[0]}, Name: {student[1]}, Average Marks: {student[7]:.2f}"
        )
    else:
        messagebox.showinfo('Student Not Found', f"No student found with Roll Number {roll_number}")


def update_student():
    try:
        roll_number, name = validate_student_identity(entry_roll.get(), entry_name.get())
    except ValueError as exc:
        messagebox.showerror('Invalid Input', str(exc))
        return

    cursor.execute('SELECT * FROM students WHERE roll_number=?', (roll_number,))
    student = cursor.fetchone()

    if not student:
        messagebox.showinfo('Student Not Found', f"No student found with Roll Number {roll_number}")
        return

    try:
        marks = parse_marks(entry.get() for entry in entry_marks)
    except ValueError as exc:
        messagebox.showerror('Invalid Input', str(exc))
        return

    average_marks = calculate_marks_average(marks)
    cursor.execute('''
        UPDATE students
        SET name=?, marks_subject1=?, marks_subject2=?, marks_subject3=?, marks_subject4=?, marks_subject5=?, average_marks=?
        WHERE roll_number=?
    ''', (name, *marks, average_marks, roll_number))
    conn.commit()
    messagebox.showinfo('Success', 'Student information updated successfully!')
    clear_entries()
    display_students()

def calculate_average():
    cursor.execute('SELECT * FROM students ORDER BY roll_number')
    students = cursor.fetchall()

    if not students:
        messagebox.showinfo('No Students', 'No students in the system to calculate average marks.')
        return

    average_text = 'Average marks recalculated from subject marks:'
    for student in students:
        marks_valid, _average_stale, computed_average = inspect_student_marks(
            student[2:7], student[7]
        )
        average_text += (
            f"\nRoll Number: {student[0]}, Name: {student[1]}, "
            f"Average Marks: {computed_average:.2f}"
            if marks_valid
            else f"\nRoll Number: {student[0]}, Name: {student[1]}, Needs review (invalid marks)"
        )
    messagebox.showinfo('Average Marks', average_text)


def calculate_grades():
    cursor.execute('SELECT * FROM students ORDER BY roll_number')
    students = cursor.fetchall()

    if not students:
        messagebox.showinfo('No Students', 'No students in the system to calculate grades.')
        return

    grades_text = 'Grades calculated from current subject marks:'
    for student in students:
        marks_valid, _average_stale, computed_average = inspect_student_marks(
            student[2:7], student[7]
        )
        if marks_valid:
            grade = grade_for_average(computed_average)
            line = f"\nRoll Number: {student[0]}, Name: {student[1]}, Grade: {grade}"
        else:
            line = (
                f"\nRoll Number: {student[0]}, Name: {student[1]}, "
                "Grade: Needs review (invalid marks)"
            )
        grades_text += line
    messagebox.showinfo('Grades', grades_text)


def sort_students():
    cursor.execute('SELECT * FROM students ORDER BY average_marks DESC, roll_number')
    students = cursor.fetchall()

    if not students:
        messagebox.showinfo('No Students', 'No students in the system to sort.')
        return

    display_students(sort_by_average=True)
    sorted_text = 'Students sorted by Average Marks:'
    for student in students:
        sorted_text += f"\nRoll Number: {student[0]}, Name: {student[1]}, Average Marks: {student[7]:.2f}"
    messagebox.showinfo('Sorted Students', sorted_text)


def save_to_file():
    cursor.execute('SELECT * FROM students ORDER BY roll_number')
    students = cursor.fetchall()

    if not students:
        messagebox.showinfo('No Students', 'No students in the system to save.')
        return

    try:
        csv_text = serialize_student_rows(students)
        with open('students_data.txt', 'w', newline='', encoding='utf-8') as file:
            file.write(csv_text)
    except (OSError, UnicodeError, ValueError) as exc:
        messagebox.showerror('Save Failed', f"Could not export student data: {exc}")
        return
    messagebox.showinfo('Data Saved', 'Student data exported to students_data.txt.')


def load_from_file():
    try:
        with open('students_data.txt', 'r', newline='', encoding='utf-8') as file:
            csv_text = file.read()

        prepared_rows = parse_student_csv_text(csv_text)
        if not prepared_rows:
            messagebox.showinfo('No Data', 'The import file contains no student records.')
            return

        # This helper validates the rows and inserts the complete batch transactionally.
        insert_student_records(conn, prepared_rows)
    except FileNotFoundError:
        messagebox.showinfo('File Not Found', 'No previous data found.')
        return
    except (OSError, UnicodeError, ValueError, sqlite3.IntegrityError) as exc:
        messagebox.showerror('Import Failed', f"Student data was not imported: {exc}")
        return

    messagebox.showinfo('Data Loaded', f"Imported {len(prepared_rows)} student record(s).")
    display_students()


def view_student_details():
    roll_number = entry_roll.get().strip()
    if not roll_number:
        messagebox.showerror('Invalid Input', 'Enter a roll number to view details.')
        return

    cursor.execute('SELECT * FROM students WHERE roll_number=?', (roll_number,))
    student = cursor.fetchone()

    if student:
        select_student_in_table(roll_number)
        details_text = (
            f"Student Details - Roll Number: {student[0]}\nName: {student[1]}\n"
            f"Marks: {student[2]}, {student[3]}, {student[4]}, {student[5]}, {student[6]}\n"
            f"Average Marks: {student[7]:.2f}"
        )
        messagebox.showinfo('Student Details', details_text)
    else:
        messagebox.showinfo('Student Not Found', f"No student found with Roll Number {roll_number}")


def remove_student():
    roll_number = entry_roll.get().strip()
    if not roll_number:
        messagebox.showerror('Invalid Input', 'Enter the roll number of the student to remove.')
        return

    cursor.execute('SELECT * FROM students WHERE roll_number=?', (roll_number,))
    student = cursor.fetchone()

    if not student:
        messagebox.showinfo('Student Not Found', f"No student found with Roll Number {roll_number}")
        return

    if not messagebox.askyesno(
        'Confirm Removal',
        f"Remove student {student[1]} (roll number {student[0]})? This cannot be undone."
    ):
        return

    cursor.execute('DELETE FROM students WHERE roll_number=?', (roll_number,))
    conn.commit()
    messagebox.showinfo('Success', f"Student with Roll Number {roll_number} removed successfully!")
    clear_entries()
    display_students()


def generate_report_cards():
    cursor.execute('SELECT * FROM students ORDER BY roll_number')
    students = cursor.fetchall()

    if not students:
        messagebox.showinfo('No Students', 'No students in the system to generate report cards.')
        return

    report_text = 'Report Cards recalculated from current subject marks:'
    for student in students:
        marks = student[2:7]
        marks_valid, _average_stale, computed_average = inspect_student_marks(marks, student[7])
        report_text += f"\n\nRoll Number: {student[0]}\nName: {student[1]}\n"
        report_text += f"Subject-wise Marks: {', '.join(_format_score(mark) for mark in marks)}\n"
        if marks_valid:
            grade = grade_for_average(computed_average)
            report_text += (
                f"Average Marks: {computed_average:.2f}\nGrade: {grade}\n"
                f"Total Marks: {sum(float(mark) for mark in marks):.2f}\n"
            )
        else:
            report_text += "Average Marks: Needs review\nGrade: Needs review\nTotal Marks: unavailable\n"
    messagebox.showinfo('Report Cards', report_text)


# Build the desktop interface.
root = tk.Tk()
root.title('Student Management System')
root.geometry('1180x760')
root.minsize(880, 600)
root.columnconfigure(0, weight=1)
root.rowconfigure(3, weight=1)

custom_font = tkfont.nametofont('TkDefaultFont').copy()
custom_font.configure(size=10)
style = ttk.Style(root)
style.configure('TButton', padding=(8, 6), font=custom_font)
style.configure('Treeview', rowheight=25, font=custom_font)
style.configure('Treeview.Heading', font=(custom_font.actual('family'), 10, 'bold'))

# Student input form
entry_frame = ttk.LabelFrame(root, text='Student details', padding=12)
entry_frame.grid(row=0, column=0, sticky='ew', padx=12, pady=(12, 6))
for column in range(5):
    entry_frame.columnconfigure(column, weight=1)

label_roll = ttk.Label(entry_frame, text='Roll Number:', font=custom_font)
label_name = ttk.Label(entry_frame, text='Name:', font=custom_font)
label_marks = [
    ttk.Label(entry_frame, text=f'Subject {i + 1} mark:', font=custom_font)
    for i in range(5)
]
entry_roll = ttk.Entry(entry_frame, font=custom_font)
entry_name = ttk.Entry(entry_frame, font=custom_font)
entry_marks = [ttk.Entry(entry_frame, font=custom_font) for _ in range(5)]

label_roll.grid(row=0, column=0, sticky='w', padx=5, pady=4)
entry_roll.grid(row=0, column=1, columnspan=4, sticky='ew', padx=5, pady=4)
label_name.grid(row=1, column=0, sticky='w', padx=5, pady=4)
entry_name.grid(row=1, column=1, columnspan=4, sticky='ew', padx=5, pady=4)
for i in range(5):
    label_marks[i].grid(row=2, column=i, sticky='w', padx=5, pady=(8, 2))
    entry_marks[i].grid(row=3, column=i, sticky='ew', padx=5, pady=2)

# Responsive action grid: buttons now belong to their actual parent frame.
button_frame = ttk.Frame(root, padding=(12, 4, 12, 8))
button_frame.grid(row=1, column=0, sticky='ew')
for column in range(4):
    button_frame.columnconfigure(column, weight=1)

button_add = ttk.Button(button_frame, text='Add Student', command=add_student)
button_display = ttk.Button(button_frame, text='Refresh List', command=display_students)
button_search = ttk.Button(button_frame, text='Search Student', command=search_student)
button_update = ttk.Button(button_frame, text='Update Student', command=update_student)
button_avg_marks = ttk.Button(button_frame, text='Student Averages', command=calculate_average)
button_grades = ttk.Button(button_frame, text='Calculate Grades', command=calculate_grades)
button_sort = ttk.Button(button_frame, text='Sort by Average', command=sort_students)
button_save = ttk.Button(button_frame, text='Export CSV', command=save_to_file)
button_load = ttk.Button(button_frame, text='Import CSV', command=load_from_file)
button_details = ttk.Button(button_frame, text='View Details', command=view_student_details)
button_remove = ttk.Button(button_frame, text='Remove Student', command=remove_student)
button_report_cards = ttk.Button(button_frame, text='Report Cards', command=generate_report_cards)

buttons = [
    (button_add, 0, 0), (button_display, 0, 1),
    (button_search, 0, 2), (button_update, 0, 3),
    (button_avg_marks, 1, 0), (button_grades, 1, 1),
    (button_sort, 1, 2), (button_save, 1, 3),
    (button_load, 2, 0), (button_details, 2, 1),
    (button_remove, 2, 2), (button_report_cards, 2, 3),
]
for button, row, column in buttons:
    button.grid(row=row, column=column, sticky='ew', padx=4, pady=4)

result_label = ttk.Label(
    root,
    text='Student records. Select a row to load it into the form.',
    font=custom_font,
)
result_label.grid(row=2, column=0, sticky='w', padx=14, pady=(2, 5))

# Scrollable table of records, including all five subject marks.
tree_frame = ttk.Frame(root, padding=(12, 0, 12, 12))
tree_frame.grid(row=3, column=0, sticky='nsew')
tree_frame.columnconfigure(0, weight=1)
tree_frame.rowconfigure(0, weight=1)

columns = (
    'roll_number', 'name', 'subject1', 'subject2', 'subject3',
    'subject4', 'subject5', 'average',
)
student_tree = ttk.Treeview(
    tree_frame, columns=columns, show='headings', selectmode='browse'
)
student_tree.tag_configure('legacy-invalid', foreground='#B42318')
column_specs = [
    ('roll_number', 'Roll number', 120),
    ('name', 'Student name', 210),
    ('subject1', 'Subject 1', 105),
    ('subject2', 'Subject 2', 105),
    ('subject3', 'Subject 3', 105),
    ('subject4', 'Subject 4', 105),
    ('subject5', 'Subject 5', 105),
    ('average', 'Average', 110),
]
for column, heading, width in column_specs:
    student_tree.heading(column, text=heading)
    student_tree.column(
        column, width=width, minwidth=85,
        stretch=(column in ('roll_number', 'name', 'average')),
        anchor='w' if column in ('roll_number', 'name') else 'center',
    )

vertical_scrollbar = ttk.Scrollbar(
    tree_frame, orient='vertical', command=student_tree.yview
)
horizontal_scrollbar = ttk.Scrollbar(
    tree_frame, orient='horizontal', command=student_tree.xview
)
student_tree.configure(
    yscrollcommand=vertical_scrollbar.set,
    xscrollcommand=horizontal_scrollbar.set,
)
student_tree.grid(row=0, column=0, sticky='nsew')
vertical_scrollbar.grid(row=0, column=1, sticky='ns')
horizontal_scrollbar.grid(row=1, column=0, sticky='ew')
student_tree.bind('<<TreeviewSelect>>', load_selected_student)

def close_application():
    try:
        conn.close()
    finally:
        root.destroy()

root.protocol('WM_DELETE_WINDOW', close_application)
display_students()
if get_database_schema_version(conn) < 1:
    messagebox.showwarning(
        'Legacy Records Need Review',
        'The existing database contains records that do not meet the current validation rules. '
        'The original table and records have been preserved, and affected rows are highlighted. '
        'Select each highlighted row, correct the name or marks, then close and reopen this app '
        'to finish the database upgrade. New entries and updates are still validated.'
    )
root.mainloop()
