"""
Simplified review agent without complex dependencies.
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..core import logger, settings
from ..models.schemas import ReviewResponse, TaskReview
from ..services import RepositoryService, ExcelService


class SimpleReviewAgent:
    """Simplified review agent for homework review."""
    
    def __init__(self):
        self.repo_service = RepositoryService()
        self.excel_service = ExcelService()
    
    async def review_student(
        self, 
        student_surname: str, 
        lecture_number: int, 
        task: Optional[str] = None
    ) -> ReviewResponse:
        """
        Review a student's homework submission.
        
        Args:
            student_surname: Student's surname
            lecture_number: Lecture number
            task: Optional specific task to review
            
        Returns:
            ReviewResponse with results
        """
        try:
            logger.info(f"Starting review for student {student_surname}, lecture {lecture_number}")
            
            if task:
                # Review specific task
                code_content = self.repo_service.read_student_code(lecture_number, task, student_surname)
                if not code_content:
                    return ReviewResponse(
                        surname=student_surname,
                        lecture_number=lecture_number,
                        average_score=0,
                        total_tasks=0,
                        details=[]
                    )
                
                # Simple review logic
                task_review = self._simple_review(task, code_content)
                
                response = ReviewResponse(
                    surname=student_surname,
                    lecture_number=lecture_number,
                    average_score=task_review.score,
                    total_tasks=1,
                    details=[task_review]
                )
            else:
                # Review all tasks in lecture
                tasks = self.repo_service.get_lecture_tasks(lecture_number)
                task_reviews = []
                
                for task_name in tasks:
                    task_number = task_name.split('_')[-1]
                    code_content = self.repo_service.read_student_code(lecture_number, task_number, student_surname)
                    
                    if code_content:
                        task_review = self._simple_review(task_number, code_content)
                        task_reviews.append(task_review)
                
                if task_reviews:
                    avg_score = sum(t.score for t in task_reviews) / len(task_reviews)
                else:
                    avg_score = 0
                
                response = ReviewResponse(
                    surname=student_surname,
                    lecture_number=lecture_number,
                    average_score=avg_score,
                    total_tasks=len(task_reviews),
                    details=task_reviews
                )
            
            # Save results
            self.excel_service.update_student_review(lecture_number, response)
            
            logger.info(f"Completed review for {student_surname}")
            return response
            
        except Exception as e:
            logger.error(f"Error reviewing student {student_surname}: {e}")
            return ReviewResponse(
                surname=student_surname,
                lecture_number=lecture_number,
                average_score=0,
                total_tasks=0,
                details=[]
            )
    
    def _simple_review(self, task: str, code_content: Dict[str, str]) -> TaskReview:
        """
        Perform a simple review based on code analysis.
        
        Args:
            task: Task identifier
            code_content: Dictionary of file paths to content
            
        Returns:
            TaskReview with results
        """
        try:
            from ..services import CodeAnalysisService
            
            # Analyze code
            analysis_service = CodeAnalysisService()
            code_summary = analysis_service.get_code_summary(code_content)
            
            # Calculate scores based on metrics
            technical_score = int(round(min(100, max(0, 100 - code_summary.get('average_complexity', 0) * 2))))
            style_score = int(round(min(100, max(0, code_summary.get('average_naming_convention_score', 0)))))
            doc_score = int(round(min(100, max(0, code_summary.get('average_docstring_coverage', 0)))))
            perf_score = 85  # Default performance score
            
            # Calculate overall score
            overall_score = int(round(technical_score * 0.4 + style_score * 0.3 + doc_score * 0.2 + perf_score * 0.1))
            
            # Generate comments
            comments = self._generate_comments(code_summary, technical_score, style_score, doc_score)
            
            return TaskReview(
                task=task,
                score=overall_score,
                comments=comments,
                technical_correctness=technical_score,
                code_style=style_score,
                documentation=doc_score,
                performance=perf_score
            )
            
        except Exception as e:
            logger.error(f"Error in simple review: {e}")
            return TaskReview(
                task=task,
                score=50,
                comments=f"Error during review: {str(e)}",
                technical_correctness=50,
                code_style=50,
                documentation=50,
                performance=50
            )
    
    def _generate_comments(self, code_summary: Dict[str, Any], tech_score: int, style_score: int, doc_score: int) -> str:
        """Generate review comments based on analysis."""
        comments = []
        
        # Technical comments
        if tech_score >= 90:
            comments.append("Excellent technical implementation with clean, efficient code.")
        elif tech_score >= 80:
            comments.append("Good technical implementation with minor areas for improvement.")
        elif tech_score >= 70:
            comments.append("Satisfactory technical implementation with some complexity issues.")
        else:
            comments.append("Technical implementation needs improvement - consider simplifying the code.")
        
        # Style comments
        if style_score >= 90:
            comments.append("Excellent code style and naming conventions.")
        elif style_score >= 80:
            comments.append("Good code style with consistent naming.")
        elif style_score >= 70:
            comments.append("Code style is acceptable but could be more consistent.")
        else:
            comments.append("Code style needs improvement - focus on consistent naming conventions.")
        
        # Documentation comments
        if doc_score >= 90:
            comments.append("Excellent documentation with comprehensive docstrings.")
        elif doc_score >= 80:
            comments.append("Good documentation with most functions documented.")
        elif doc_score >= 70:
            comments.append("Adequate documentation but could benefit from more docstrings.")
        else:
            comments.append("Documentation needs improvement - add docstrings to functions and classes.")
        
        # Performance comments
        comments.append("Performance appears adequate for the task requirements.")
        
        return " ".join(comments)


class SimpleLectureReviewAgent:
    """Simplified agent for reviewing entire lectures."""
    
    def __init__(self):
        self.repo_service = RepositoryService()
        self.excel_service = ExcelService()
    
    async def review_lecture(
        self, 
        lecture_number: int, 
        students: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Review an entire lecture.
        
        Args:
            lecture_number: Lecture number
            students: Optional list of specific students to review
            
        Returns:
            Dictionary with lecture review results
        """
        try:
            logger.info(f"Starting lecture review for lecture {lecture_number}")
            
            # Get students to review
            if students:
                students_to_review = students
            else:
                students_to_review = self.repo_service.get_all_students_in_lecture(lecture_number)
            
            if not students_to_review:
                return {
                    "lecture_number": lecture_number,
                    "total_students": 0,
                    "average_score": 0,
                    "student_results": []
                }
            
            # Review each student
            student_results = []
            review_agent = SimpleReviewAgent()
            
            for student in students_to_review:
                try:
                    result = await review_agent.review_student(student, lecture_number)
                    student_results.append(result)
                    logger.info(f"Reviewed student {student}")
                except Exception as e:
                    logger.error(f"Error reviewing student {student}: {e}")
            
            # Calculate summary statistics
            if student_results:
                total_score = sum(result.average_score for result in student_results)
                average_score = total_score / len(student_results)
            else:
                average_score = 0
            
            return {
                "lecture_number": lecture_number,
                "total_students": len(student_results),
                "average_score": average_score,
                "student_results": student_results
            }
            
        except Exception as e:
            logger.error(f"Error reviewing lecture {lecture_number}: {e}")
            return {
                "lecture_number": lecture_number,
                "total_students": 0,
                "average_score": 0,
                "student_results": []
            }
