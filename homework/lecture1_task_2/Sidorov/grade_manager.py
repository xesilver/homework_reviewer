# Task 2: Student Grade Manager
# Student: Sidorov

def add_student(name, id):
    return {"name": name, "id": id, "grades": []}

def add_grade(student, grade):
    student["grades"].append(grade)

def get_average(student):
    if student["grades"]:
        return sum(student["grades"]) / len(student["grades"])
    return 0

def print_student(student):
    print(f"Name: {student['name']}")
    print(f"ID: {student['id']}")
    print(f"Grades: {student['grades']}")
    print(f"Average: {get_average(student)}")

# Example usage
s1 = add_student("Alice", "001")
add_grade(s1, 85)
add_grade(s1, 90)
print_student(s1)
