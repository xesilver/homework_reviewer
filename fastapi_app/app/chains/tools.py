"""
LangChain tools for homework review process.
"""
from typing import Dict, List, Optional, Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from ..services import CodeAnalysisService, RepositoryService
from ..core import logger


class CodeAnalysisInput(BaseModel):
    """Input for code analysis tool."""
    file_path: str = Field(description="Path to the code file")
    content: str = Field(description="Content of the code file")


class CodeAnalysisTool(BaseTool):
    """Tool for analyzing code quality and extracting metrics."""
    
    name: str = "code_analysis"
    description: str = "Analyze code quality and extract metrics like complexity, style, and documentation"
    args_schema: Type[CodeAnalysisInput] = CodeAnalysisInput
    
    def __init__(self):
        super().__init__()
        self.analysis_service = CodeAnalysisService()
    
    def _run(self, file_path: str, content: str) -> str:
        """Run code analysis on the given file."""
        try:
            from pathlib import Path
            metrics = self.analysis_service.analyze_code_file(Path(file_path), content)
            
            result = f"""
Code Analysis Results for {file_path}:
- Lines of Code: {metrics.lines_of_code}
- Lines of Comments: {metrics.lines_of_comments}
- Functions Count: {metrics.functions_count}
- Classes Count: {metrics.classes_count}
- Complexity Score: {metrics.complexity_score}
- Docstring Coverage: {metrics.docstring_coverage:.1f}%
- Naming Convention Score: {metrics.naming_convention_score:.1f}%
"""
            return result
        except Exception as e:
            logger.error(f"Error in code analysis: {e}")
            return f"Error analyzing code: {str(e)}"
    
    async def _arun(self, file_path: str, content: str) -> str:
        """Async version of code analysis."""
        return self._run(file_path, content)


class RepositoryExplorerInput(BaseModel):
    """Input for repository explorer tool."""
    lecture_number: int = Field(description="Lecture number to explore")
    task: Optional[str] = Field(default=None, description="Specific task to explore")


class RepositoryExplorerTool(BaseTool):
    """Tool for exploring homework repository structure."""
    
    name: str = "repository_explorer"
    description: str = "Explore homework repository structure and find student submissions"
    args_schema: Type[RepositoryExplorerInput] = RepositoryExplorerInput
    
    def __init__(self):
        super().__init__()
        self.repo_service = RepositoryService()
    
    def _run(self, lecture_number: int, task: Optional[str] = None) -> str:
        """Explore repository structure."""
        try:
            if task:
                # Get students for specific task
                students = self.repo_service.get_student_submissions(lecture_number, task)
                result = f"Students who submitted lecture{lecture_number}_task_{task}:\n"
                for student in students:
                    result += f"- {student}\n"
            else:
                # Get all tasks for lecture
                tasks = self.repo_service.get_lecture_tasks(lecture_number)
                result = f"Tasks in lecture {lecture_number}:\n"
                for task_name in tasks:
                    students = self.repo_service.get_student_submissions(lecture_number, task_name.split('_')[-1])
                    result += f"- {task_name}: {len(students)} students\n"
            
            return result
        except Exception as e:
            logger.error(f"Error exploring repository: {e}")
            return f"Error exploring repository: {str(e)}"
    
    async def _arun(self, lecture_number: int, task: Optional[str] = None) -> str:
        """Async version of repository exploration."""
        return self._run(lecture_number, task)


class CodeReaderInput(BaseModel):
    """Input for code reader tool."""
    lecture_number: int = Field(description="Lecture number")
    task: str = Field(description="Task identifier")
    student_surname: str = Field(description="Student's surname")


class CodeReaderTool(BaseTool):
    """Tool for reading student code submissions."""
    
    name: str = "code_reader"
    description: str = "Read student code submissions for a specific task"
    args_schema: Type[CodeReaderInput] = CodeReaderInput
    
    def __init__(self):
        super().__init__()
        self.repo_service = RepositoryService()
    
    def _run(self, lecture_number: int, task: str, student_surname: str) -> str:
        """Read student code for a specific task."""
        try:
            code_content = self.repo_service.read_student_code(lecture_number, task, student_surname)
            
            if not code_content:
                return f"No code found for student {student_surname} in lecture{lecture_number}_task_{task}"
            
            result = f"Code submission for {student_surname} (lecture{lecture_number}_task_{task}):\n\n"
            for file_path, content in code_content.items():
                result += f"=== {file_path} ===\n{content}\n\n"
            
            return result
        except Exception as e:
            logger.error(f"Error reading code: {e}")
            return f"Error reading code: {str(e)}"
    
    async def _arun(self, lecture_number: int, task: str, student_surname: str) -> str:
        """Async version of code reading."""
        return self._run(lecture_number, task, student_surname)


class ScoreCalculatorInput(BaseModel):
    """Input for score calculator tool."""
    technical_correctness: int = Field(ge=0, le=100, description="Technical correctness score")
    code_style: int = Field(ge=0, le=100, description="Code style score")
    documentation: int = Field(ge=0, le=100, description="Documentation score")
    performance: int = Field(ge=0, le=100, description="Performance score")
    weights: Optional[Dict[str, float]] = Field(default=None, description="Custom weights for scoring")


class ScoreCalculatorTool(BaseTool):
    """Tool for calculating weighted scores."""
    
    name: str = "score_calculator"
    description: str = "Calculate weighted overall score from individual criteria scores"
    args_schema: Type[ScoreCalculatorInput] = ScoreCalculatorInput
    
    def _run(
        self, 
        technical_correctness: int, 
        code_style: int, 
        documentation: int, 
        performance: int,
        weights: Optional[Dict[str, float]] = None
    ) -> str:
        """Calculate weighted overall score."""
        try:
            # Default weights
            default_weights = {
                "technical_correctness": 0.4,
                "code_style": 0.3,
                "documentation": 0.2,
                "performance": 0.1
            }
            
            if weights:
                default_weights.update(weights)
            
            # Calculate weighted score
            overall_score = (
                technical_correctness * default_weights["technical_correctness"] +
                code_style * default_weights["code_style"] +
                documentation * default_weights["documentation"] +
                performance * default_weights["performance"]
            )
            
            result = f"""
Score Calculation:
- Technical Correctness: {technical_correctness} (weight: {default_weights['technical_correctness']})
- Code Style: {code_style} (weight: {default_weights['code_style']})
- Documentation: {documentation} (weight: {default_weights['documentation']})
- Performance: {performance} (weight: {default_weights['performance']})

Overall Score: {overall_score:.1f}
"""
            return result
        except Exception as e:
            logger.error(f"Error calculating score: {e}")
            return f"Error calculating score: {str(e)}"
    
    async def _arun(
        self, 
        technical_correctness: int, 
        code_style: int, 
        documentation: int, 
        performance: int,
        weights: Optional[Dict[str, float]] = None
    ) -> str:
        """Async version of score calculation."""
        return self._run(technical_correctness, code_style, documentation, performance, weights)


class ReviewValidatorInput(BaseModel):
    """Input for review validator tool."""
    score: int = Field(ge=0, le=100, description="Score to validate")
    comments: str = Field(description="Comments to validate")


class ReviewValidatorTool(BaseTool):
    """Tool for validating review results."""
    
    name: str = "review_validator"
    description: str = "Validate review results for consistency and completeness"
    args_schema: Type[ReviewValidatorInput] = ReviewValidatorInput
    
    def _run(self, score: int, comments: str) -> str:
        """Validate review results."""
        try:
            issues = []
            
            # Check score validity
            if score < 0 or score > 100:
                issues.append(f"Invalid score: {score} (must be 0-100)")
            
            # Check comments
            if not comments or len(comments.strip()) < 10:
                issues.append("Comments too short or empty")
            
            if len(comments) > 1000:
                issues.append("Comments too long")
            
            # Check for constructive feedback
            if any(word in comments.lower() for word in ["terrible", "awful", "horrible"]):
                issues.append("Comments may be too harsh - consider constructive feedback")
            
            if not any(word in comments.lower() for word in ["good", "well", "excellent", "improve", "suggestion"]):
                issues.append("Comments should include positive feedback or suggestions")
            
            if issues:
                return "Review validation issues found:\n" + "\n".join(f"- {issue}" for issue in issues)
            else:
                return "Review validation passed - no issues found"
                
        except Exception as e:
            logger.error(f"Error validating review: {e}")
            return f"Error validating review: {str(e)}"
    
    async def _arun(self, score: int, comments: str) -> str:
        """Async version of review validation."""
        return self._run(score, comments)


# Tool registry
def get_review_tools() -> List[BaseTool]:
    """Get all available review tools."""
    return [
        CodeAnalysisTool(),
        RepositoryExplorerTool(),
        CodeReaderTool(),
        ScoreCalculatorTool(),
        ReviewValidatorTool()
    ]