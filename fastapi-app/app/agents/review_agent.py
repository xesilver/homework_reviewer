"""
LangGraph agents and workflow definitions for homework review.
"""
from typing import Dict, List, Any, Optional, TypedDict, Annotated

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from ..core import logger, settings
from ..models.schemas import ReviewResponse, TaskReview
from ..services import RepositoryService, ExcelService
from ..chains.review_chains import ReviewChain, BatchReviewChain, LectureSummaryChain


class ReviewState(TypedDict):
    """State for the review workflow."""
    # Input parameters
    student_surname: Annotated[str, lambda x, y: y]
    lecture_number: Annotated[int, lambda x, y: y]
    task: Annotated[Optional[str], lambda x, y: y]
    
    # Workflow state
    current_step: Annotated[str, lambda x, y: y]
    error_message: Annotated[Optional[str], lambda x, y: y]
    
    # Data
    code_content: Annotated[Dict[str, str], lambda x, y: y]
    code_metrics: Annotated[Dict[str, Any], lambda x, y: y]
    review_result: Annotated[Optional[Dict[str, Any]], lambda x, y: y]
    
    # Output
    final_response: Annotated[Optional[ReviewResponse], lambda x, y: y]


class LectureReviewState(TypedDict):
    """State for lecture-wide review workflow."""
    # Input parameters
    lecture_number: Annotated[int, lambda x, y: y]
    students: Annotated[Optional[List[str]], lambda x, y: y]
    
    # Workflow state
    current_step: Annotated[str, lambda x, y: y]
    error_message: Annotated[Optional[str], lambda x, y: y]
    progress: Annotated[float, lambda x, y: y]
    
    # Data
    tasks: Annotated[List[str], lambda x, y: y]
    student_results: Annotated[List[Dict[str, Any]], lambda x, y: y]
    
    # Output
    final_response: Annotated[Optional[Dict[str, Any]], lambda x, y: y]


class HomeworkReviewAgent:
    """Main agent for homework review workflow."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            openai_api_key=settings.openai_api_key,
            model_name=settings.openai_model,
            temperature=0.1
        )
        self.repo_service = RepositoryService()
        self.excel_service = ExcelService()
        self.review_chain = ReviewChain(self.llm)
        
        # Create the workflow graph
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create the review workflow graph."""
        workflow = StateGraph(ReviewState)
        
        # Add nodes
        workflow.add_node("validate_input", self._validate_input)
        workflow.add_node("get_code", self._get_student_code)
        workflow.add_node("analyze_code", self._analyze_code)
        workflow.add_node("review_code", self._review_code)
        workflow.add_node("calculate_score", self._calculate_score)
        workflow.add_node("save_results", self._save_results)
        workflow.add_node("handle_error", self._handle_error)
        
        # Set entry point
        workflow.set_entry_point("validate_input")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "validate_input",
            lambda state: "handle_error" if state.get("error_message") else "get_code",
        )
        workflow.add_conditional_edges(
            "get_code",
            lambda state: "handle_error" if state.get("error_message") else "analyze_code",
        )
        workflow.add_conditional_edges(
            "analyze_code",
            lambda state: "handle_error" if state.get("error_message") else "review_code",
        )
        workflow.add_conditional_edges(
            "review_code",
            lambda state: "handle_error" if state.get("error_message") else "calculate_score",
        )
        workflow.add_conditional_edges(
            "calculate_score",
            lambda state: "handle_error" if state.get("error_message") else "save_results",
        )
        
        workflow.add_edge("save_results", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def _validate_input(self, state: ReviewState) -> ReviewState:
        """Validate input parameters."""
        try:
            if not state["student_surname"]:
                state["error_message"] = "Student surname is required"
                return state
            
            if not state["lecture_number"] or state["lecture_number"] < 1:
                state["error_message"] = "Valid lecture number is required"
                return state
            
            state["current_step"] = "validation_complete"
            logger.info(f"Input validation passed for {state['student_surname']}")
            return state
            
        except Exception as e:
            state["error_message"] = f"Validation error: {str(e)}"
            logger.error(f"Input validation failed: {e}")
            return state
    
    def _get_student_code(self, state: ReviewState) -> ReviewState:
        """Get student code for the task."""
        try:
            if state.get("task"):
                # Review specific task
                code_content = self.repo_service.read_student_code(
                    state["lecture_number"], 
                    state["task"], 
                    state["student_surname"]
                )
            else:
                # Review all tasks in lecture
                tasks = self.repo_service.get_lecture_tasks(state["lecture_number"])
                code_content = {}
                for task in tasks:
                    task_number = task.split('_')[-1]
                    task_code = self.repo_service.read_student_code(
                        state["lecture_number"], 
                        task_number, 
                        state["student_surname"]
                    )
                    code_content.update(task_code)
            
            if not code_content:
                state["error_message"] = f"No code found for student {state['student_surname']}"
                return state
            
            state["code_content"] = code_content
            state["current_step"] = "code_retrieved"
            logger.info(f"Retrieved code for {state['student_surname']}")
            return state
            
        except Exception as e:
            state["error_message"] = f"Error retrieving code: {str(e)}"
            logger.error(f"Code retrieval failed: {e}")
            return state
    
    def _analyze_code(self, state: ReviewState) -> ReviewState:
        """Analyze code metrics."""
        try:
            from ..services import CodeAnalysisService
            analysis_service = CodeAnalysisService()
            
            code_metrics = analysis_service.get_code_summary(state["code_content"])
            state["code_metrics"] = code_metrics
            
            state["current_step"] = "code_analyzed"
            logger.info(f"Code analysis completed for {state['student_surname']}")
            return state
            
        except Exception as e:
            state["error_message"] = f"Error analyzing code: {str(e)}"
            logger.error(f"Code analysis failed: {e}")
            return state
    
    def _review_code(self, state: ReviewState) -> ReviewState:
        """Review the code using AI."""
        try:
            if state.get("task"):
                # Review specific task
                review_result = self.review_chain.review_student_task(
                    state["student_surname"],
                    state["lecture_number"],
                    state["task"]
                )
            else:
                # Review all tasks
                tasks = self.repo_service.get_lecture_tasks(state["lecture_number"])
                review_results = []
                
                for task in tasks:
                    task_number = task.split('_')[-1]
                    task_result = self.review_chain.review_student_task(
                        state["student_surname"],
                        state["lecture_number"],
                        task_number
                    )
                    review_results.append(task_result)
                
                # Combine results
                if review_results:
                    avg_score = sum(r.get('score', 0) for r in review_results) / len(review_results)
                    review_result = {
                        "average_score": avg_score,
                        "task_results": review_results
                    }
                else:
                    review_result = {"average_score": 0, "task_results": []}
            
            state["review_result"] = review_result
            state["current_step"] = "code_reviewed"
            logger.info(f"Code review completed for {state['student_surname']}")
            return state
            
        except Exception as e:
            state["error_message"] = f"Error reviewing code: {str(e)}"
            logger.error(f"Code review failed: {e}")
            return state
    
    def _calculate_score(self, state: ReviewState) -> ReviewState:
        """Calculate final scores and prepare response."""
        try:
            review_result = state["review_result"]
            
            if state.get("task"):
                # Single task review
                task_review = TaskReview(
                    task=state["task"],
                    score=int(round(review_result.get("score", 0))),
                    comments=review_result.get("comments", ""),
                    technical_correctness=int(round(review_result.get("technical_correctness", 0))),
                    code_style=int(round(review_result.get("code_style", 0))),
                    documentation=int(round(review_result.get("documentation", 0))),
                    performance=int(round(review_result.get("performance", 0)))
                )
                
                response = ReviewResponse(
                    surname=state["student_surname"],
                    lecture_number=state["lecture_number"],
                    average_score=review_result.get("score", 0),
                    total_tasks=1,
                    details=[task_review]
                )
            else:
                # Multiple tasks review
                task_reviews = []
                for task_result in review_result.get("task_results", []):
                    task_review = TaskReview(
                        task=task_result.get("task", "unknown"),
                        score=int(round(task_result.get("score", 0))),
                        comments=task_result.get("comments", ""),
                        technical_correctness=int(round(task_result.get("technical_correctness", 0))),
                        code_style=int(round(task_result.get("code_style", 0))),
                        documentation=int(round(task_result.get("documentation", 0))),
                        performance=int(round(task_result.get("performance", 0)))
                    )
                    task_reviews.append(task_review)
                
                response = ReviewResponse(
                    surname=state["student_surname"],
                    lecture_number=state["lecture_number"],
                    average_score=review_result.get("average_score", 0),
                    total_tasks=len(task_reviews),
                    details=task_reviews
                )
            
            state["final_response"] = response
            state["current_step"] = "score_calculated"
            logger.info(f"Score calculation completed for {state['student_surname']}")
            return state
            
        except Exception as e:
            state["error_message"] = f"Error calculating score: {str(e)}"
            logger.error(f"Score calculation failed: {e}")
            return state
    
    def _save_results(self, state: ReviewState) -> ReviewState:
        """Save results to Excel file."""
        try:
            response = state["final_response"]
            self.excel_service.update_student_review(
                state["lecture_number"], 
                response
            )
            
            state["current_step"] = "results_saved"
            logger.info(f"Results saved for {state['student_surname']}")
            return state
            
        except Exception as e:
            state["error_message"] = f"Error saving results: {str(e)}"
            logger.error(f"Results saving failed: {e}")
            return state
    
    def _handle_error(self, state: ReviewState) -> ReviewState:
        """Handle errors in the workflow."""
        error_message = state.get("error_message", "Unknown error")
        logger.error(f"Workflow error: {error_message}")
        
        # Create error response
        error_response = ReviewResponse(
            surname=state["student_surname"],
            lecture_number=state["lecture_number"],
            average_score=0,
            total_tasks=0,
            details=[]
        )
        
        state["final_response"] = error_response
        return state
    
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
        initial_state = ReviewState(
            student_surname=student_surname,
            lecture_number=lecture_number,
            task=task,
            current_step="start",
            error_message=None,
            code_content={},
            code_metrics={},
            review_result=None,
            final_response=None
        )
        
        try:
            result = await self.workflow.ainvoke(initial_state)
            return result["final_response"]
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return ReviewResponse(
                surname=student_surname,
                lecture_number=lecture_number,
                average_score=0,
                total_tasks=0,
                details=[]
            )


class LectureReviewAgent:
    """Agent for reviewing entire lectures."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            openai_api_key=settings.openai_api_key,
            model_name=settings.openai_model,
            temperature=0.1
        )
        self.repo_service = RepositoryService()
        self.excel_service = ExcelService()
        self.batch_review_chain = BatchReviewChain(self.llm)
        self.summary_chain = LectureSummaryChain(self.llm)
        
        # Create the workflow graph
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create the lecture review workflow graph."""
        workflow = StateGraph(LectureReviewState)
        
        # Add nodes
        workflow.add_node("validate_input", self._validate_input)
        workflow.add_node("get_students", self._get_students)
        workflow.add_node("get_tasks", self._get_tasks)
        workflow.add_node("review_students", self._review_students)
        workflow.add_node("generate_summary", self._generate_summary)
        workflow.add_node("save_results", self._save_results)
        workflow.add_node("handle_error", self._handle_error)
        
        # Add edges
        workflow.set_entry_point("validate_input")
        
        workflow.add_conditional_edges(
            "validate_input",
            lambda state: "handle_error" if state.get("error_message") else "get_students",
        )
        workflow.add_conditional_edges(
            "get_students",
            lambda state: "handle_error" if state.get("error_message") else "get_tasks",
        )
        workflow.add_conditional_edges(
            "get_tasks",
            lambda state: "handle_error" if state.get("error_message") else "review_students",
        )
        workflow.add_conditional_edges(
            "review_students",
            lambda state: "handle_error" if state.get("error_message") else "generate_summary",
        )
        workflow.add_conditional_edges(
            "generate_summary",
            lambda state: "handle_error" if state.get("error_message") else "save_results",
        )
        workflow.add_edge("save_results", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def _validate_input(self, state: LectureReviewState) -> LectureReviewState:
        """Validate input parameters."""
        try:
            if not state["lecture_number"] or state["lecture_number"] < 1:
                state["error_message"] = "Valid lecture number is required"
                return state
            
            state["current_step"] = "validation_complete"
            logger.info(f"Lecture review validation passed for lecture {state['lecture_number']}")
            return state
            
        except Exception as e:
            state["error_message"] = f"Validation error: {str(e)}"
            logger.error(f"Lecture validation failed: {e}")
            return state
    
    def _get_students(self, state: LectureReviewState) -> LectureReviewState:
        """Get students to review."""
        try:
            if state.get("students"):
                students = state["students"]
            else:
                students = self.repo_service.get_all_students_in_lecture(state["lecture_number"])
            
            if not students:
                state["error_message"] = f"No students found for lecture {state['lecture_number']}"
                return state
            
            state["students"] = students
            state["current_step"] = "students_retrieved"
            logger.info(f"Retrieved {len(students)} students for lecture {state['lecture_number']}")
            return state
            
        except Exception as e:
            state["error_message"] = f"Error retrieving students: {str(e)}"
            logger.error(f"Student retrieval failed: {e}")
            return state
    
    def _get_tasks(self, state: LectureReviewState) -> LectureReviewState:
        """Get tasks for the lecture."""
        try:
            tasks = self.repo_service.get_lecture_tasks(state["lecture_number"])
            
            if not tasks:
                state["error_message"] = f"No tasks found for lecture {state['lecture_number']}"
                return state
            
            state["tasks"] = tasks
            state["current_step"] = "tasks_retrieved"
            logger.info(f"Retrieved {len(tasks)} tasks for lecture {state['lecture_number']}")
            return state
            
        except Exception as e:
            state["error_message"] = f"Error retrieving tasks: {str(e)}"
            logger.error(f"Task retrieval failed: {e}")
            return state
    
    async def _review_students(self, state: LectureReviewState) -> LectureReviewState:
        """Review all students' submissions."""
        try:
            student_results = []
            total_students = len(state["students"])
            
            for i, student in enumerate(state["students"]):
                try:
                    # Create individual review agent
                    review_agent = HomeworkReviewAgent()
                    
                    # Review student
                    result = await review_agent.review_student(
                        student, 
                        state["lecture_number"]
                    )
                    
                    student_results.append({
                        "student": student,
                        "result": result
                    })
                    
                    # Update progress
                    state["progress"] = (i + 1) / total_students * 100
                    logger.info(f"Reviewed student {student} ({i+1}/{total_students})")
                    
                except Exception as e:
                    logger.error(f"Error reviewing student {student}: {e}")
                    student_results.append({
                        "student": student,
                        "error": str(e)
                    })
            
            state["student_results"] = student_results
            state["current_step"] = "students_reviewed"
            logger.info(f"Completed review of {len(student_results)} students")
            return state
            
        except Exception as e:
            state["error_message"] = f"Error reviewing students: {str(e)}"
            logger.error(f"Student review failed: {e}")
            return state
    
    def _generate_summary(self, state: LectureReviewState) -> LectureReviewState:
        """Generate lecture summary."""
        try:
            summary = self.summary_chain.generate_lecture_summary(
                state["lecture_number"],
                state["student_results"]
            )
            
            state["summary"] = summary
            state["current_step"] = "summary_generated"
            logger.info(f"Generated summary for lecture {state['lecture_number']}")
            return state
            
        except Exception as e:
            state["error_message"] = f"Error generating summary: {str(e)}"
            logger.error(f"Summary generation failed: {e}")
            return state
    
    def _save_results(self, state: LectureReviewState) -> LectureReviewState:
        """Save all results."""
        try:
            # Results are already saved by individual review agents
            state["current_step"] = "results_saved"
            logger.info(f"All results saved for lecture {state['lecture_number']}")
            return state
            
        except Exception as e:
            state["error_message"] = f"Error saving results: {str(e)}"
            logger.error(f"Results saving failed: {e}")
            return state
    
    def _handle_error(self, state: LectureReviewState) -> LectureReviewState:
        """Handle errors in the workflow."""
        error_message = state.get("error_message", "Unknown error")
        logger.error(f"Lecture workflow error: {error_message}")
        
        state["final_response"] = {
            "error": error_message,
            "lecture_number": state["lecture_number"],
            "student_results": []
        }
        return state
    
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
        initial_state = LectureReviewState(
            lecture_number=lecture_number,
            students=students,
            current_step="start",
            error_message=None,
            progress=0.0,
            tasks=[],
            student_results=[],
            final_response=None
        )
        
        try:
            result = await self.workflow.ainvoke(initial_state)
            return result.get("final_response", {})
        except Exception as e:
            logger.error(f"Lecture workflow execution failed: {e}")
            return {
                "error": str(e),
                "lecture_number": lecture_number,
                "student_results": []
            }