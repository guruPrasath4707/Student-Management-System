import tkinter as tk
from tkinter import ttk, messagebox
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


def search_student():
    roll_number = entry_roll.get()
    cursor.execute('SELECT * FROM students WHERE roll_number=?', (roll_number,))
    student = cursor.fetchone()

    if student:
        messagebox.showinfo('Student Found', f"Roll Number: {student[0]}, Name: {student[1]}, Average Marks: {student[7]:.2f}")
    else:
        messagebox.showinfo('Student Not Found', f"No student found with Roll Number {roll_number}")


def update_student():
    roll_number = entry_roll.get()
    cursor.execute('SELECT * FROM students WHERE roll_number=?', (roll_number,))
    student = cursor.fetchone()

    if student:
        name = entry_name.get()
        marks = [float(entry_marks[i].get()) for i in range(5)]

        average_marks = sum(marks) / len(marks)

        cursor.execute('''
            UPDATE students
            SET name=?, marks_subject1=?, marks_subject2=?, marks_subject3=?, marks_subject4=?, marks_subject5=?, average_marks=?
            WHERE roll_number=?
        ''', (name, *marks, average_marks, roll_number))
        conn.commit()
        messagebox.showinfo('Success', 'Student information updated successfully!')
        clear_entries()
        display_students()
    else:
        messagebox.showinfo('Student Not Found', f"No student found with Roll Number {roll_number}")


def calculate_average():
    cursor.execute('SELECT * FROM students')
    students = cursor.fetchall()

    if not students:
        messagebox.showinfo('No Students', 'No students in the system to calculate average marks.')
    else:
        average_text = 'Average Marks of all students:'
        for student in students:
            average_text += f"\nRoll Number: {student[0]}, Name: {student[1]}, Average Marks: {student[7]:.2f}"
        messagebox.showinfo('Average Marks', average_text)


def calculate_grades():
    cursor.execute('SELECT * FROM students')
    students = cursor.fetchall()

    if not students:
        messagebox.showinfo('No Students', 'No students in the system to calculate grades.')
    else:
        grades_text = 'Grades of all students:'
        for student in students:
            average_marks = student[7]
            grade = 'A' if average_marks >= 90 else \
                    'B' if 80 <= average_marks < 90 else \
                    'C' if 70 <= average_marks < 80 else \
                    'D' if 60 <= average_marks < 70 else 'F'
            grades_text += f"\nRoll Number: {student[0]}, Name: {student[1]}, Grade: {grade}"
        messagebox.showinfo('Grades', grades_text)


def sort_students():
    cursor.execute('SELECT * FROM students ORDER BY average_marks DESC')
    students = cursor.fetchall()

    if not students:
        messagebox.showinfo('No Students', 'No students in the system to sort.')
    else:
        sorted_text = 'Students sorted by Average Marks:'
        for student in students:
            sorted_text += f"\nRoll Number: {student[0]}, Name: {student[1]}, Average Marks: {student[7]:.2f}"
        messagebox.showinfo('Sorted Students', sorted_text)


def save_to_file():
    cursor.execute('SELECT * FROM students')
    students = cursor.fetchall()

    if not students:
        messagebox.showinfo('No Students', 'No students in the system to save.')
    else:
        with open('students_data.txt', 'w') as file:
            for student in students:
                file.write(f"{student[0]},{student[1]},{student[2]},{student[3]},{student[4]},{student[5]},{student[6]},{student[7]}\n")
        messagebox.showinfo('Data Saved', 'Data saved successfully!')


def load_from_file():
    try:
        with open('students_data.txt', 'r') as file:
            for line in file:
                data = line.strip().split(',')
                cursor.execute('''
                    INSERT INTO students (roll_number, name, marks_subject1, marks_subject2, marks_subject3, marks_subject4, marks_subject5, average_marks)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (data[0], data[1], float(data[2]), float(data[3]), float(data[4]), float(data[5]), float(data[6]), float(data[7])))
            conn.commit()
        messagebox.showinfo('Data Loaded', 'Data loaded successfully!')
        display_students()
    except FileNotFoundError:
        messagebox.showinfo('File Not Found', 'No previous data found.')


def view_student_details():
    roll_number = entry_roll.get()
    cursor.execute('SELECT * FROM students WHERE roll_number=?', (roll_number,))
    student = cursor.fetchone()

    if student:
        details_text = f"\nStudent Details - Roll Number: {student[0]}\nName: {student[1]}\nMarks: {student[2]}, {student[3]}, {student[4]}, {student[5]}, {student[6]}\nAverage Marks: {student[7]:.2f}"
        messagebox.showinfo('Student Details', details_text)
    else:
        messagebox.showinfo('Student Not Found', f"No student found with Roll Number {roll_number}")


def remove_student():
    roll_number = entry_roll.get()
    cursor.execute('SELECT * FROM students WHERE roll_number=?', (roll_number,))
    student = cursor.fetchone()

    if student:
        cursor.execute('DELETE FROM students WHERE roll_number=?', (roll_number,))
        conn.commit()
        messagebox.showinfo('Success', f"Student with Roll Number {roll_number} removed successfully!")
        clear_entries()
        display_students()
    else:
        messagebox.showinfo('Student Not Found', f"No student found with Roll Number {roll_number}")


def generate_report_cards():
    cursor.execute('SELECT * FROM students')
    students = cursor.fetchall()

    if not students:
        messagebox.showinfo('No Students', 'No students in the system to generate report cards.')
    else:
        report_text = 'Report Cards for all students:'
        for student in students:
            report_text += f"\n\nRoll Number: {student[0]}\nName: {student[1]}\nAverage Marks: {student[7]:.2f}\n"
            average_marks = student[7]
            grade = 'A' if average_marks >= 90 else \
                    'B' if 80 <= average_marks < 90 else \
                    'C' if 70 <= average_marks < 80 else \
                    'D' if 60 <= average_marks < 70 else 'F'
            report_text += f"Grade: {grade}\nSubject-wise Marks: {student[2]}, {student[3]}, {student[4]}, {student[5]}, {student[6]}\nTotal Marks: {sum(student[2:7])}\n"
        messagebox.showinfo('Report Cards', report_text)


# Create the main window
root = tk.Tk()
root.title('Student Management System')

# Set custom font (replace 'YourFont.ttf' with the actual font file name)
custom_font = tk.font.Font(family='YourFont', size=10)
style = ttk.Style()
style.configure('TButton', padding=5, relief='flat', background='#3498db', foreground='white', font=custom_font)
style.map('TButton', background=[('active', '#2980b9')])

# Create and set variables
result_text = tk.StringVar()

# Create a frame for entry widgets
entry_frame = ttk.Frame(root, padding=(10, 10, 10, 0))
entry_frame.grid(row=0, column=0, columnspan=2)

# Create labels, entry widgets, and buttons
label_roll = ttk.Label(entry_frame, text='Roll Number:', font=custom_font)
label_name = ttk.Label(entry_frame, text='Name:', font=custom_font)
label_marks = [ttk.Label(entry_frame, text=f'Marks Subject {i + 1}:', font=custom_font) for i in range(5)]

entry_roll = ttk.Entry(entry_frame, font=custom_font)
entry_name = ttk.Entry(entry_frame, font=custom_font)
entry_marks = [ttk.Entry(entry_frame, font=custom_font) for _ in range(5)]

button_add = ttk.Button(root, text='Add Student', command=add_student)
button_display = ttk.Button(root, text='Display Students', command=display_students)
button_search = ttk.Button(root, text='Search Student', command=search_student)
button_update = ttk.Button(root, text='Update Student', command=update_student)
button_avg_marks = ttk.Button(root, text='Calculate Average Marks', command=calculate_average)
button_grades = ttk.Button(root, text='Calculate Grades', command=calculate_grades)
button_sort = ttk.Button(root, text='Sort Students', command=sort_students)
button_save = ttk.Button(root, text='Save to File', command=save_to_file)
button_load = ttk.Button(root, text='Load from File', command=load_from_file)
button_details = ttk.Button(root, text='View Student Details', command=view_student_details)
button_remove = ttk.Button(root, text='Remove Student', command=remove_student)
button_report_cards = ttk.Button(root, text='Generate Report Cards', command=generate_report_cards)

# Set the layout using grid
label_roll.grid(row=0, column=0, padx=5, pady=5)
entry_roll.grid(row=0, column=1, padx=5, pady=5)
label_name.grid(row=1, column=0, padx=5, pady=5)
entry_name.grid(row=1, column=1, padx=5, pady=5)

for i in range(5):
    label_marks[i].grid(row=2, column=i, padx=5, pady=5)
    entry_marks[i].grid(row=3, column=i, padx=5, pady=5)

# Create a frame for action buttons
button_frame = ttk.Frame(root, padding=(10, 10, 10, 10))
button_frame.grid(row=1, column=0, columnspan=2)

button_add.grid(row=0, column=0, padx=5, pady=5)
button_display.grid(row=0, column=1, padx=5, pady=5)
button_search.grid(row=0, column=2, padx=5, pady=5)
button_update.grid(row=0, column=3, padx=5, pady=5)
button_avg_marks.grid(row=0, column=4, padx=5, pady=5)
button_grades.grid(row=0, column=5, padx=5, pady=5)
button_sort.grid(row=0, column=6, padx=5, pady=5)
button_save.grid(row=0, column=7, padx=5, pady=5)
button_load.grid(row=0, column=8, padx=5, pady=5)
button_details.grid(row=0, column=9, padx=5, pady=5)
button_remove.grid(row=0, column=10, padx=5, pady=5)
button_report_cards.grid(row=0, column=11, padx=5, pady=5)

# Create a text widget for displaying results
result_label = ttk.Label(root, text='Student Information:', font=custom_font)
result_label.grid(row=2, column=0, columnspan=2, pady=(10, 0))

result_display = ttk.Label(root, textvariable=result_text, justify='left', font=custom_font)
result_display.grid(row=3, column=0, columnspan=2, pady=(0, 10))

# Start the main loop
root.mainloop()

# Close the database connection when the program exits
conn.close()
