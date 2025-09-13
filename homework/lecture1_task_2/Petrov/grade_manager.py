# Task 2: Student Grade Manager
# Student: Petrov

class Student:
    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.grades = []
    
    def add_grade(self, grade):
        if 0 <= grade <= 100:
            self.grades.append(grade)
        else:
            print("Invalid grade")
    
    def get_average(self):
        if self.grades:
            return sum(self.grades) / len(self.grades)
        return 0
    
    def show_grades(self):
        print(f"Student: {self.name}")
        print(f"Grades: {self.grades}")
        print(f"Average: {self.get_average()}")

# Test the class
student = Student("John", "123")
student.add_grade(85)
student.add_grade(90)
student.add_grade(78)
student.show_grades()
