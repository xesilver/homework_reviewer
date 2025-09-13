"""
LangChain chains for homework review workflow.
"""
from typing import Dict, List, Any, Optional
from langchain.chains import LLMChain
from langchain_openai import OpenAI
from langchain.schema import BaseOutputParser
from langchain.callbacks import BaseCallbackHandler
from pydantic import BaseModel, Field

from ..core import logger, settings
from ..services import CodeAnalysisService, RepositoryService
from .prompts import (
    review_prompt,
    quick_review_prompt,
    code_analysis_prompt,
    task_specific_prompt,
    batch_review_prompt,
    lecture_summary_prompt,
    ReviewOutputParser
)
from .tools import get_review_tools


class ReviewChain:
    """Main chain for homework review process."""
    
    def __init__(self, llm: Optional[OpenAI] = None):
        self.llm = llm or OpenAI(
            openai_api_key=settings.openai_api_key,
            model_name=settings.openai_model,
            temperature=0.1
        )
        self.code_analysis_service = CodeAnalysisService()
        self.repo_service = RepositoryService()
        self.output_parser = ReviewOutputParser()
        
        # Create chains
        self.review_chain = LLMChain(
            llm=self.llm,
            prompt=review_prompt,
            output_parser=self.output_parser
        )
        
        self.quick_review_chain = LLMChain(
            llm=self.llm,
            prompt=quick_review_prompt
        )
        
        self.code_analysis_chain = LLMChain(
            llm=self.llm,
            prompt=code_analysis_prompt
        )
    
    def review_student_task(
        self, 
        student_surname: str, 
        lecture_number: int, 
        task: str,
        task_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Review a specific student's task submission.
        
        Args:
            student_surname: Student's surname
            lecture_number: Lecture number
            task: Task identifier
            task_description: Optional task description
            
        Returns:
            Dictionary with review results
        """
        try:
            # Get student code
            code_content = self.repo_service.read_student_code(lecture_number, task, student_surname)
            
            if not code_content:
                return {
                    "error": f"No code found for student {student_surname} in task {task}",
                    "score": 0,
                    "comments": "No submission found"
                }
            
            # Analyze code metrics
            code_summary = self.code_analysis_service.get_code_summary(code_content)
            
            # Prepare input for review chain
            chain_input = {
                "student_surname": student_surname,
                "lecture_number": lecture_number,
                "task_name": task,
                "task_description": task_description or f"Task {task}",
                "code_content": self._format_code_content(code_content),
                "code_metrics": self._format_code_metrics(code_summary)
            }
            
            # Run review chain
            result = self.review_chain.run(**chain_input)
            
            # Parse result
            if isinstance(result, dict):
                review_result = result
            else:
                review_result = self.output_parser.parse(str(result))
            
            return {
                "task": task,
                "score": review_result.overall_score,
                "comments": review_result.comments,
                "technical_correctness": review_result.technical_correctness,
                "code_style": review_result.code_style,
                "documentation": review_result.documentation,
                "performance": review_result.performance,
                "code_metrics": code_summary
            }
            
        except Exception as e:
            logger.error(f"Error reviewing student task: {e}")
            return {
                "error": str(e),
                "task": task,
                "score": 0,
                "comments": f"Error during review: {str(e)}"
            }
    
    def quick_review(
        self, 
        student_surname: str, 
        task: str, 
        code_content: str
    ) -> Dict[str, Any]:
        """
        Perform a quick review of code submission.
        
        Args:
            student_surname: Student's surname
            task: Task identifier
            code_content: Code content to review
            
        Returns:
            Dictionary with quick review results
        """
        try:
            result = self.quick_review_chain.run(
                student_surname=student_surname,
                task_name=task,
                code_content=code_content
            )
            
            # Parse result (simplified)
            lines = result.strip().split('\n')
            score = 80  # Default
            comments = "Quick review completed"
            
            for line in lines:
                if line.lower().startswith('score:'):
                    try:
                        score = int(line.split(':')[1].strip())
                    except:
                        pass
                elif line.lower().startswith('comments:'):
                    comments = line.split(':', 1)[1].strip()
            
            return {
                "score": score,
                "comments": comments,
                "review_type": "quick"
            }
            
        except Exception as e:
            logger.error(f"Error in quick review: {e}")
            return {
                "error": str(e),
                "score": 0,
                "comments": f"Error during quick review: {str(e)}"
            }
    
    def analyze_code(self, code_content: str) -> str:
        """
        Analyze code and provide insights.
        
        Args:
            code_content: Code content to analyze
            
        Returns:
            Analysis results as string
        """
        try:
            result = self.code_analysis_chain.run(code_content=code_content)
            return result
        except Exception as e:
            logger.error(f"Error analyzing code: {e}")
            return f"Error analyzing code: {str(e)}"
    
    def _format_code_content(self, code_content: Dict[str, str]) -> str:
        """Format code content for prompt."""
        formatted = ""
        for file_path, content in code_content.items():
            formatted += f"=== {file_path} ===\n{content}\n\n"
        return formatted
    
    def _format_code_metrics(self, code_summary: Dict[str, Any]) -> str:
        """Format code metrics for prompt."""
        metrics = f"""
Code Metrics Summary:
- Total Files: {code_summary['total_files']}
- Lines of Code: {code_summary['total_lines_of_code']}
- Lines of Comments: {code_summary['total_lines_of_comments']}
- Functions: {code_summary['total_functions']}
- Classes: {code_summary['total_classes']}
- Average Complexity: {code_summary['average_complexity']:.1f}
- Docstring Coverage: {code_summary['average_docstring_coverage']:.1f}%
- Naming Convention Score: {code_summary['average_naming_convention_score']:.1f}%
"""
        return metrics


class BatchReviewChain:
    """Chain for reviewing multiple students' submissions."""
    
    def __init__(self, llm: Optional[OpenAI] = None):
        self.llm = llm or OpenAI(
            openai_api_key=settings.openai_api_key,
            model_name=settings.openai_model,
            temperature=0.1
        )
        self.repo_service = RepositoryService()
        self.batch_review_chain = LLMChain(
            llm=self.llm,
            prompt=batch_review_prompt
        )
    
    def review_lecture_task(
        self, 
        lecture_number: int, 
        task: str,
        task_description: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Review all students' submissions for a specific task.
        
        Args:
            lecture_number: Lecture number
            task: Task identifier
            task_description: Optional task description
            
        Returns:
            List of review results for each student
        """
        try:
            # Get all students who submitted this task
            students = self.repo_service.get_student_submissions(lecture_number, task)
            
            if not students:
                return []
            
            # Prepare submissions data
            submissions_data = []
            for student in students:
                code_content = self.repo_service.read_student_code(lecture_number, task, student)
                if code_content:
                    formatted_code = self._format_code_content(code_content)
                    submissions_data.append(f"Student: {student}\nCode:\n{formatted_code}\n")
            
            # Run batch review
            submissions_text = "\n".join(submissions_data)
            result = self.batch_review_chain.run(
                task_name=task,
                task_description=task_description or f"Task {task}",
                submissions=submissions_text
            )
            
            # Parse results (simplified)
            reviews = []
            lines = result.strip().split('\n')
            current_student = None
            current_score = 80
            current_comments = "Batch review completed"
            
            for line in lines:
                if line.lower().startswith('student:'):
                    if current_student:
                        reviews.append({
                            "student": current_student,
                            "score": current_score,
                            "comments": current_comments
                        })
                    current_student = line.split(':')[1].strip()
                elif line.lower().startswith('score:'):
                    try:
                        current_score = int(line.split(':')[1].strip())
                    except:
                        pass
                elif line.lower().startswith('comments:'):
                    current_comments = line.split(':', 1)[1].strip()
            
            # Add last student
            if current_student:
                reviews.append({
                    "student": current_student,
                    "score": current_score,
                    "comments": current_comments
                })
            
            return reviews
            
        except Exception as e:
            logger.error(f"Error in batch review: {e}")
            return []
    
    def _format_code_content(self, code_content: Dict[str, str]) -> str:
        """Format code content for batch review."""
        formatted = ""
        for file_path, content in code_content.items():
            formatted += f"File: {file_path}\n{content}\n"
        return formatted


class LectureSummaryChain:
    """Chain for generating lecture-wide summaries."""
    
    def __init__(self, llm: Optional[OpenAI] = None):
        self.llm = llm or OpenAI(
            openai_api_key=settings.openai_api_key,
            model_name=settings.openai_model,
            temperature=0.1
        )
        self.summary_chain = LLMChain(
            llm=self.llm,
            prompt=lecture_summary_prompt
        )
    
    def generate_lecture_summary(
        self, 
        lecture_number: int, 
        student_results: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a summary for a lecture review.
        
        Args:
            lecture_number: Lecture number
            student_results: List of student review results
            
        Returns:
            Summary text
        """
        try:
            total_students = len(student_results)
            if total_students == 0:
                return "No students reviewed for this lecture."
            
            # Calculate average score
            total_score = sum(result.get('score', 0) for result in student_results)
            average_score = total_score / total_students
            
            # Format student results
            results_text = ""
            for result in student_results:
                results_text += f"- {result.get('student', 'Unknown')}: {result.get('score', 0)} - {result.get('comments', 'No comments')}\n"
            
            # Generate summary
            summary = self.summary_chain.run(
                lecture_number=lecture_number,
                total_students=total_students,
                average_score=average_score,
                student_results=results_text
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating lecture summary: {e}")
            return f"Error generating summary: {str(e)}"
