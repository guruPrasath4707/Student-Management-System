# Initialize an empty dictionary to store student information
students_data = {}

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
        # Get input from the user
        roll_number = input("Enter student's roll number: ")
        name = input("Enter student's name: ")

        # Initialize an empty list to store marks
        marks_list = []

        # Loop to take marks input for 5 subjects
        for subject_num in range(1, 6):
            marks = float(input(f"Enter marks for subject {subject_num}: "))
            marks_list.append(marks)

        # Calculate average marks
        average_marks = sum(marks_list) / len(marks_list)

        # Store student information in a dictionary
        student_info = {'Name': name, 'Marks': marks_list, 'Average Marks': average_marks}

        # Add the student to the main dictionary using roll number as key
        students_data[roll_number] = student_info

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
        # Update student information
        roll_number = input("Enter the roll number to update: ")
        if roll_number in students_data:
            name = input("Enter updated name: ")
            
            # Loop to take updated marks input for 5 subjects
            updated_marks_list = []
            for subject_num in range(1, 6):
                updated_marks = float(input(f"Enter updated marks for subject {subject_num}: "))
                updated_marks_list.append(updated_marks)

            # Calculate updated average marks
            updated_average_marks = sum(updated_marks_list) / len(updated_marks_list)
            students_data[roll_number]['Name'] = name
            students_data[roll_number]['Marks'] = updated_marks_list
            students_data[roll_number]['Average Marks'] = updated_average_marks

            print(f"\nStudent information for Roll Number {roll_number} updated successfully.\n")
        else:
            print(f"\nNo student found with Roll Number {roll_number}.\n")

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
                grade = 'A' if average_marks >= 90 else \
                        'B' if 80 <= average_marks < 90 else \
                        'C' if 70 <= average_marks < 80 else \
                        'D' if 60 <= average_marks < 70 else 'F'
                print(f"Roll Number: {roll}, Name: {info['Name']}, Grade: {grade}")

    elif choice == '7':
        # Sort students based on average marks
        sorted_students = sorted(students_data.items(), key=lambda x: x[1]['Average Marks'], reverse=True)
        print("\nStudents sorted by Average Marks:")
        for roll, info in sorted_students:
            print(f"Roll Number: {roll}, Name: {info['Name']}, Average Marks: {info['Average Marks']:.2f}")

    elif choice == '8':
        # Save data to a file
        with open('students_data.txt', 'w') as file:
            for roll, info in students_data.items():
                file.write(f"{roll},{info['Name']},{','.join(map(str, info['Marks']))},{info['Average Marks']}\n")
        print("Data saved successfully!")

    elif choice == '9':
        # Load data from a file
        try:
            with open('students_data.txt', 'r') as file:
                for line in file:
                    data = line.strip().split(',')
                    roll_number = data[0]
                    name = data[1]
                    marks_list = list(map(float, data[2].split(',')))
                    average_marks = float(data[3])
                    student_info = {'Name': name, 'Marks': marks_list, 'Average Marks': average_marks}
                    students_data[roll_number] = student_info
            print("Data loaded successfully!")
        except FileNotFoundError:
            print("No previous data found.")

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
                grade = 'A' if average_marks >= 90 else \
                        'B' if 80 <= average_marks < 90 else \
                        'C' if 70 <= average_marks < 80 else \
                        'D' if 60 <= average_marks < 70 else 'F'
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
