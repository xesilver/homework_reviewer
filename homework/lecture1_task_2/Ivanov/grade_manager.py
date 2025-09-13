# Task 2: Student Grade Manager
# Student: Ivanov

class Student:
    """
    A class to represent a student and manage their grades.
    """
    
    def __init__(self, name, student_id):
        """
        Initialize a new student.
        
        Args:
            name (str): Student's name
            student_id (str): Student's ID
        """
        self.name = name
        self.student_id = student_id
        self.grades = {}
    
    def add_grade(self, subject, grade):
        """
        Add a grade for a subject.
        
        Args:
            subject (str): Subject name
            grade (float): Grade (0-100)
            
        Raises:
            ValueError: If grade is not between 0 and 100
        """
        if not 0 <= grade <= 100:
            raise ValueError("Grade must be between 0 and 100")
        self.grades[subject] = grade
    
    def get_average_grade(self):
        """
        Calculate the average grade.
        
        Returns:
            float: Average grade, or 0 if no grades
        """
        if not self.grades:
            return 0
        return sum(self.grades.values()) / len(self.grades)
    
    def get_grade_report(self):
        """
        Generate a grade report.
        
        Returns:
            str: Formatted grade report
        """
        report = f"Grade Report for {self.name} (ID: {self.student_id})\n"
        report += "=" * 40 + "\n"
        
        if not self.grades:
            report += "No grades recorded.\n"
        else:
            for subject, grade in self.grades.items():
                report += f"{subject}: {grade}\n"
            report += f"\nAverage Grade: {self.get_average_grade():.2f}\n"
        
        return report


class GradeManager:
    """
    A class to manage multiple students' grades.
    """
    
    def __init__(self):
        """Initialize the grade manager."""
        self.students = {}
    
    def add_student(self, name, student_id):
        """
        Add a new student to the manager.
        
        Args:
            name (str): Student's name
            student_id (str): Student's ID
            
        Returns:
            Student: The created student object
        """
        student = Student(name, student_id)
        self.students[student_id] = student
        return student
    
    def get_student(self, student_id):
        """
        Get a student by ID.
        
        Args:
            student_id (str): Student's ID
            
        Returns:
            Student: Student object, or None if not found
        """
        return self.students.get(student_id)
    
    def get_class_average(self):
        """
        Calculate the class average grade.
        
        Returns:
            float: Class average grade
        """
        if not self.students:
            return 0
        
        total_average = sum(student.get_average_grade() for student in self.students.values())
        return total_average / len(self.students)


def main():
    """Main function to demonstrate the grade manager."""
    manager = GradeManager()
    
    # Add some students
    student1 = manager.add_student("Alice Johnson", "S001")
    student2 = manager.add_student("Bob Smith", "S002")
    
    # Add grades
    student1.add_grade("Math", 85)
    student1.add_grade("Science", 92)
    student1.add_grade("English", 78)
    
    student2.add_grade("Math", 90)
    student2.add_grade("Science", 88)
    student2.add_grade("English", 95)
    
    # Display reports
    print(student1.get_grade_report())
    print("\n" + "="*50 + "\n")
    print(student2.get_grade_report())
    
    print(f"\nClass Average: {manager.get_class_average():.2f}")


if __name__ == "__main__":
    main()
