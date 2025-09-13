"""
File I/O and repository management services.
"""
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from ..core import logger, ensure_directory, is_code_file, sanitize_filename
from ..core.config import settings


class RepositoryService:
    """Service for managing homework repository structure."""
    
    def __init__(self, homework_dir: Optional[Path] = None):
        self.homework_dir = homework_dir or settings.homework_dir
        ensure_directory(self.homework_dir)
    
    def get_lecture_tasks(self, lecture_number: int) -> List[str]:
        """
        Get all task directories for a specific lecture.
        
        Args:
            lecture_number: Lecture number
            
        Returns:
            List of task directory names
        """
        lecture_pattern = f"lecture{lecture_number}_task_*"
        task_dirs = []
        
        for item in self.homework_dir.iterdir():
            if item.is_dir() and item.name.startswith(f"lecture{lecture_number}_task_"):
                task_dirs.append(item.name)
        
        return sorted(task_dirs)
    
    def get_student_submissions(self, lecture_number: int, task: str) -> List[str]:
        """
        Get all student submissions for a specific task.
        
        Args:
            lecture_number: Lecture number
            task: Task identifier
            
        Returns:
            List of student surnames who submitted the task
        """
        task_dir = self.homework_dir / f"lecture{lecture_number}_task_{task}"
        if not task_dir.exists():
            return []
        
        students = []
        for item in task_dir.iterdir():
            if item.is_dir():
                students.append(item.name)
        
        return sorted(students)
    
    def get_student_task_files(self, lecture_number: int, task: str, student_surname: str) -> List[Path]:
        """
        Get all code files for a specific student's task submission.
        
        Args:
            lecture_number: Lecture number
            task: Task identifier
            student_surname: Student's surname
            
        Returns:
            List of file paths for the student's submission
        """
        student_dir = self.homework_dir / f"lecture{lecture_number}_task_{task}" / student_surname
        if not student_dir.exists():
            return []
        
        code_files = []
        for file_path in student_dir.rglob("*"):
            if file_path.is_file() and is_code_file(file_path):
                code_files.append(file_path)
        
        return sorted(code_files)
    
    def read_student_code(self, lecture_number: int, task: str, student_surname: str) -> Dict[str, str]:
        """
        Read all code files for a student's task submission.
        
        Args:
            lecture_number: Lecture number
            task: Task identifier
            student_surname: Student's surname
            
        Returns:
            Dictionary mapping file paths to file contents
        """
        files = self.get_student_task_files(lecture_number, task, student_surname)
        code_content = {}
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                code_content[str(file_path.relative_to(self.homework_dir))] = content
            except Exception as e:
                logger.warning(f"Failed to read file {file_path}: {e}")
                code_content[str(file_path.relative_to(self.homework_dir))] = f"Error reading file: {e}"
        
        return code_content
    
    def get_all_students_in_lecture(self, lecture_number: int) -> List[str]:
        """
        Get all students who have submissions in a lecture.
        
        Args:
            lecture_number: Lecture number
            
        Returns:
            List of unique student surnames
        """
        tasks = self.get_lecture_tasks(lecture_number)
        all_students = set()
        
        for task in tasks:
            task_number = task.split('_')[-1]  # Extract task number
            students = self.get_student_submissions(lecture_number, task_number)
            all_students.update(students)
        
        return sorted(list(all_students))
    
    def validate_repository_structure(self) -> Dict[str, List[str]]:
        """
        Validate the repository structure and return any issues found.
        
        Returns:
            Dictionary with validation results
        """
        issues = {
            "missing_directories": [],
            "empty_tasks": [],
            "no_students": [],
            "invalid_structure": []
        }
        
        if not self.homework_dir.exists():
            issues["missing_directories"].append(str(self.homework_dir))
            return issues
        
        # Check for lecture directories
        lecture_dirs = [d for d in self.homework_dir.iterdir() if d.is_dir() and d.name.startswith("lecture")]
        
        if not lecture_dirs:
            issues["no_students"].append("No lecture directories found")
            return issues
        
        # Group task directories by lecture number
        lecture_tasks = {}
        for task_dir in lecture_dirs:
            try:
                # Extract lecture number from task directory name
                task_name = task_dir.name
                if not task_name.startswith("lecture") or "_task_" not in task_name:
                    issues["invalid_structure"].append(f"Invalid task directory name: {task_name}")
                    continue
                
                lecture_number = int(task_name.split("_")[0].replace("lecture", ""))
                
                if lecture_number not in lecture_tasks:
                    lecture_tasks[lecture_number] = []
                lecture_tasks[lecture_number].append(task_dir)
                    
            except (ValueError, IndexError) as e:
                issues["invalid_structure"].append(f"Error parsing task directory {task_dir.name}: {e}")
        
        # Check each lecture
        for lecture_number, task_dirs in lecture_tasks.items():
            if not task_dirs:
                issues["empty_tasks"].append(f"Lecture {lecture_number} has no task directories")
                continue
            
            # Check student submissions
            has_students = False
            for task_dir in task_dirs:
                student_dirs = [d for d in task_dir.iterdir() if d.is_dir()]
                if student_dirs:
                    has_students = True
                    break
            
            if not has_students:
                issues["no_students"].append(f"Lecture {lecture_number} has no student submissions")
        
        return issues
    
    def create_sample_structure(self, lecture_number: int, task_count: int = 2) -> None:
        """
        Create a sample repository structure for testing.
        
        Args:
            lecture_number: Lecture number
            task_count: Number of tasks to create
        """
        for task_num in range(1, task_count + 1):
            task_dir = self.homework_dir / f"lecture{lecture_number}_task_{task_num}"
            ensure_directory(task_dir)
            
            # Create sample student directories
            sample_students = ["Ivanov", "Petrov", "Sidorov"]
            for student in sample_students:
                student_dir = task_dir / student
                ensure_directory(student_dir)
                
                # Create sample code files
                sample_files = {
                    "main.py": "# Sample Python code\nprint('Hello, World!')",
                    "utils.py": "# Utility functions\ndef helper():\n    pass",
                    "README.md": "# Task Description\nThis is a sample task."
                }
                
                for filename, content in sample_files.items():
                    file_path = student_dir / filename
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
        
        logger.info(f"Created sample structure for lecture {lecture_number} with {task_count} tasks")
