import tkinter as tk
from tkinter import messagebox
import sqlite3

from student_core import calculate_average as calculate_marks_average, parse_marks, validate_student_identity

# Open the per-user database, migrating the old working-directory file once when present.
from student_storage import StorageError, connect_database

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

def display_students():
    cursor.execute('SELECT * FROM students')
    students = cursor.fetchall()
    result_text.set('')

    for student in students:
        result_text.set(result_text.get() +
                       f"\nRoll Number: {student[0]}, Name: {student[1]}, Average Marks: {student[7]:.2f}\n")


def clear_entries():
    entry_roll.delete(0, tk.END)
    entry_name.delete(0, tk.END)
    for entry in entry_marks:
        entry.delete(0, tk.END)

# Create the main window
root = tk.Tk()
root.title('Student Management System')

# Create and set variables
result_text = tk.StringVar()

# Create labels, entry widgets, and buttons
label_roll = tk.Label(root, text='Roll Number:')
label_name = tk.Label(root, text='Name:')
label_marks = [tk.Label(root, text=f'Marks Subject {i + 1}:') for i in range(5)]

entry_roll = tk.Entry(root)
entry_name = tk.Entry(root)
entry_marks = [tk.Entry(root) for _ in range(5)]

button_add = tk.Button(root, text='Add Student', command=add_student)
button_display = tk.Button(root, text='Display Students', command=display_students)

# Set the layout using grid
label_roll.grid(row=0, column=0)
entry_roll.grid(row=0, column=1)
label_name.grid(row=1, column=0)
entry_name.grid(row=1, column=1)

for i in range(5):
    label_marks[i].grid(row=2 + i, column=0)
    entry_marks[i].grid(row=2 + i, column=1)

button_add.grid(row=7, column=0, columnspan=2)
button_display.grid(row=8, column=0, columnspan=2)

# Create a text widget for displaying results
result_label = tk.Label(root, text='Student Information:')
result_label.grid(row=9, column=0, columnspan=2)

result_display = tk.Label(root, textvariable=result_text, justify='left')
result_display.grid(row=10, column=0, columnspan=2)

# Start the main loop
root.mainloop()

# Close the database connection when the program exits
conn.close()
