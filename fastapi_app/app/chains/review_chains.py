from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

from ..core import logger, settings
from ..services import CodeAnalysisService
from .prompts import (
    review_prompt,
    ReviewOutputParser
)


class ReviewChain:
    """Main chain for homework review process."""

    def __init__(self, llm: Optional[ChatGoogleGenerativeAI] = None):
        self.llm = llm or ChatGoogleGenerativeAI(
            google_api_key=settings.google_api_key,
            model=settings.gemini_model,
            temperature=0.1,
            convert_system_message_to_human=True
        )
        self.code_analysis_service = CodeAnalysisService()
        self.output_parser = ReviewOutputParser()

        # Create chains
        self.review_chain = review_prompt | self.llm | StrOutputParser() | self.output_parser

    def review_student_task(
        self,
        student_surname: str,
        lecture_number: int,
        task: str,
        code_content: Dict[str, str],
        task_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Review a specific student's task submission using the provided code.
        """
        try:
            if not code_content:
                return {
                    "error": f"No code found for student {student_surname} in task {task}",
                    "score": 0,
                    "comments": "No submission found"
                }

            code_summary = self.code_analysis_service.get_code_summary(code_content)

            chain_input = {
                "student_surname": student_surname,
                "lecture_number": lecture_number,
                "task_name": task,
                "task_description": task_description or f"Task {task}",
                "code_content": self._format_code_content(code_content),
                "code_metrics": self._format_code_metrics(code_summary)
            }

            review_result = self.review_chain.invoke(chain_input)

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

    def _format_code_content(self, code_content: Dict[str, str]) -> str:
        """Format code content for prompt."""
        formatted = ""
        for file_path, content in code_content.items():
            formatted += f"=== {file_path} ===\n{content}\n\n"
        return formatted

    def _format_code_metrics(self, code_summary: Dict[str, Any]) -> str:
        """Format code metrics for prompt."""
        return f"""
Code Metrics Summary:
- Total Files: {code_summary.get('total_files', 0)}
- Lines of Code: {code_summary.get('total_lines_of_code', 0)}
- Lines of Comments: {code_summary.get('total_lines_of_comments', 0)}
- Functions: {code_summary.get('total_functions', 0)}
- Classes: {code_summary.get('total_classes', 0)}
- Average Complexity: {code_summary.get('average_complexity', 0):.1f}
- Docstring Coverage: {code_summary.get('average_docstring_coverage', 0):.1f}%
- Naming Convention Score: {code_summary.get('average_naming_convention_score', 0):.1f}%
"""