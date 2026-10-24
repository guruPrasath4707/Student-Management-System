import csv
from student_core import calculate_average, grade_for_average, parse_marks, validate_student_identity
from student_data_io import parse_student_csv_text, serialize_student_rows

# Initialize an empty dictionary to store student information
students_data = {}

def prompt_marks(prompt_prefix):
    """Read and validate exactly five subject marks without crashing the menu."""
    entered = [
        input(f"{prompt_prefix} {subject_num}: ")
        for subject_num in range(1, 6)
    ]
    try:
        return parse_marks(entered)
    except ValueError as exc:
        print(f"Invalid marks: {exc}")
        return None


# Main menu loop
while True:
    # Display the main menu options
    print("\nStudent Management System Menu:")
    print("1. Add Student")
    print("2. Display Students")
    print("3. Search for a Student")
    print("4. Update Student Information")
    print("5. Calculate Average Marks")
    print("6. Calculate Grades")
    print("7. Sort Students by Average Marks")
    print("8. Save Data to File")
    print("9. Load Data from File")
    print("10. View Student Details")
    print("11. Remove Student")
    print("12. Generate Report Card")
    print("13. Exit")

    # Get user input for the menu choice
    choice = input("Enter your choice (1-13): ")

    # Perform actions based on user choice
    if choice == '1':
        roll_number = input("Enter student's roll number: ")
        name = input("Enter student's name: ")
        try:
            roll_number, name = validate_student_identity(roll_number, name)
        except ValueError as exc:
            print(f"Invalid student details: {exc}")
            continue
        if roll_number in students_data:
            print(f"A student with roll number {roll_number} already exists.")
            continue

        marks_list = prompt_marks("Enter marks for subject")
        if marks_list is None:
            print("Student was not added.")
            continue

        average_marks = calculate_average(marks_list)
        students_data[roll_number] = {
            'Name': name,
            'Marks': marks_list,
            'Average Marks': average_marks,
        }
        print("\nStudent added successfully!\n")
    elif choice == '2':
        # Check if there are any students in the system
        if not students_data:
            print("\nNo students in the system.\n")
        else:
            # Display the list of students
            print("\nStudent List:")
            for roll, info in students_data.items():
                total_marks = sum(info['Marks'])
                print(f"\nRoll Number: {roll}\nName: {info['Name']}\nAverage Marks: {info['Average Marks']:.2f}\nTotal Marks: {total_marks}")

    elif choice == '3':
        # Search for a student
        roll_number = input("Enter the roll number to search: ")
        student_info = students_data.get(roll_number)
        if student_info:
            print(f"\nStudent found!\nRoll Number: {roll_number}\nName: {student_info['Name']}\nAverage Marks: {student_info['Average Marks']}")
        else:
            print(f"\nNo student found with Roll Number {roll_number}.\n")

    elif choice == '4':
        roll_number = input("Enter the roll number to update: ").strip()
        if not roll_number:
            print("Roll number is required.")
            continue
        if roll_number not in students_data:
            print(f"No student found with Roll Number {roll_number}.")
            continue

        name = input("Enter updated name: ")
        try:
            roll_number, name = validate_student_identity(roll_number, name)
        except ValueError as exc:
            print(f"Invalid student details: {exc}")
            continue
        updated_marks_list = prompt_marks("Enter updated marks for subject")
        if updated_marks_list is None:
            print("Student information was not changed.")
            continue

        updated_average_marks = calculate_average(updated_marks_list)
        students_data[roll_number]['Name'] = name
        students_data[roll_number]['Marks'] = updated_marks_list
        students_data[roll_number]['Average Marks'] = updated_average_marks
        print(f"\nStudent information for Roll Number {roll_number} updated successfully.\n")
    elif choice == '5':
        # Calculate the average marks of all students
        if not students_data:
            print("No students in the system to calculate average marks.")
        else:
            print("\nAverage Marks of all students:")
            for roll, info in students_data.items():
                print(f"Roll Number: {roll}, Name: {info['Name']}, Average Marks: {info['Average Marks']:.2f}")

    elif choice == '6':
        # Calculate grades for all students
        if not students_data:
            print("No students in the system to calculate grades.")
        else:
            print("\nGrades of all students:")
            for roll, info in students_data.items():
                average_marks = info['Average Marks']
                grade = grade_for_average(average_marks)
                print(f"Roll Number: {roll}, Name: {info['Name']}, Grade: {grade}")

    elif choice == '7':
        # Sort students based on average marks
        sorted_students = sorted(students_data.items(), key=lambda x: x[1]['Average Marks'], reverse=True)
        print("\nStudents sorted by Average Marks:")
        for roll, info in sorted_students:
            print(f"Roll Number: {roll}, Name: {info['Name']}, Average Marks: {info['Average Marks']:.2f}")

    elif choice == '8':
        records = [
            (roll, info['Name'], *info['Marks'], info['Average Marks'])
            for roll, info in sorted(students_data.items())
        ]
        try:
            csv_text = serialize_student_rows(records)
            with open('students_data.txt', 'w', newline='', encoding='utf-8') as file:
                file.write(csv_text)
            print("Data saved successfully!")
        except (OSError, UnicodeError, ValueError) as exc:
            print(f"Data save failed: {exc}")

    elif choice == '9':
        try:
            with open('students_data.txt', 'r', newline='', encoding='utf-8') as file:
                csv_text = file.read()
            loaded_records = parse_student_csv_text(csv_text)
        except FileNotFoundError:
            print("No previous data found.")
            continue
        except (OSError, UnicodeError, ValueError, csv.Error) as exc:
            print(f"Data load failed. No records were changed: {exc}")
            continue

        if not loaded_records:
            print("The data file contains no student records.")
            continue

        # Never replace a record already present in the active in-memory store.
        conflicting_rolls = {record[0] for record in loaded_records if record[0] in students_data}
        if conflicting_rolls:
            print(
                f"Data load aborted: {len(conflicting_rolls)} roll number(s) already exist "
                "in memory. No records were changed."
            )
            continue

        # Parsing validates the entire file before this loop changes the dictionary.
        for record in loaded_records:
            roll_number, name, *tail = record
            marks_list, average_marks = tail[:5], tail[5]
            students_data[roll_number] = {
                'Name': name,
                'Marks': list(marks_list),
                'Average Marks': average_marks,
            }
        print(f"Data loaded successfully ({len(loaded_records)} records).")

    elif choice == '10':
        # View detailed information of a student
        roll_number = input("Enter the roll number to view details: ")
        student_info = students_data.get(roll_number)
        if student_info:
            print(f"\nStudent Details\nRoll Number: {roll_number}\nName: {student_info['Name']}\nMarks: {', '.join(map(str, student_info['Marks']))}\nAverage Marks: {student_info['Average Marks']:.2f}")
        else:
            print(f"No student found with Roll Number {roll_number}.")

    elif choice == '11':
        # Remove a student
        roll_number = input("Enter the roll number to remove: ")
        if roll_number in students_data:
            del students_data[roll_number]
            print(f"Student with Roll Number {roll_number} removed successfully.")
        else:
            print(f"No student found with Roll Number {roll_number}.")

    elif choice == '12':
        # Generate report cards for all students
        if not students_data:
            print("No students in the system to generate report cards.")
        else:
            print("\nReport Cards for all students:")
            for roll, info in students_data.items():
                print(f"\nRoll Number: {roll}")
                print(f"Name: {info['Name']}")
                print(f"Average Marks: {info['Average Marks']:.2f}")
                average_marks = info['Average Marks']
                grade = grade_for_average(average_marks)
                print(f"Grade: {grade}")
                print("Subject-wise Marks:")
                for subject_num, marks in enumerate(info['Marks'], start=1):
                    print(f"Subject {subject_num}: {marks}")
                total_marks = sum(info['Marks'])
                print(f"Total Marks: {total_marks}")

    elif choice == '13':
        # Exit the program
        print("Exiting the program. Goodbye!")
        break

    else:
        # Handle invalid choices
        print("Invalid choice. Please enter a number between 1 and 13.")
