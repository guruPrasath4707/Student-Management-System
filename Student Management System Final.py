import tkinter as tk
from tkinter import messagebox
import sqlite3

# Create a SQLite database connection
conn = sqlite3.connect('students_database.db')
cursor = conn.cursor()

# Create a table to store student information
cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        roll_number TEXT PRIMARY KEY,
        name TEXT,
        marks_subject1 REAL,
        marks_subject2 REAL,
        marks_subject3 REAL,
        marks_subject4 REAL,
        marks_subject5 REAL,
        average_marks REAL
    )
''')
conn.commit()


def add_student():
    roll_number = entry_roll.get()
    name = entry_name.get()
    marks = [float(entry_marks[i].get()) for i in range(5)]

    average_marks = sum(marks) / len(marks)

    try:
        cursor.execute('''
            INSERT INTO students (roll_number, name, marks_subject1, marks_subject2, marks_subject3, marks_subject4, marks_subject5, average_marks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (roll_number, name, *marks, average_marks))
        conn.commit()
        messagebox.showinfo('Success', 'Student added successfully!')
    except sqlite3.IntegrityError:
        messagebox.showerror('Error', 'Student with the same roll number already exists!')


def display_students():
    cursor.execute('SELECT * FROM students')
    students = cursor.fetchall()
    result_text.set('')

    for student in students:
        result_text.set(result_text.get() +
                       f"\nRoll Number: {student[0]}, Name: {student[1]}, Average Marks: {student[7]:.2f}\n")


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
