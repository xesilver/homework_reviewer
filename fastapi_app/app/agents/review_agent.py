from typing import Dict, Any, Optional, TypedDict
from collections import defaultdict

from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI

from ..core import logger, settings
from ..models.schemas import ReviewResponse, TaskReview
from ..services import RepositoryService, ExcelService
from ..chains.review_chains import ReviewChain


class ReviewState(TypedDict):
    """State for the review workflow."""
    username: str
    lecture_number: int
    task: Optional[str]
    current_step: str
    error_message: Optional[str]
    code_content: Dict[str, str]
    code_metrics: Dict[str, Any]
    review_result: Optional[Dict[str, Any]]
    final_response: Optional[ReviewResponse]


class HomeworkReviewAgent:
    """Main agent for homework review workflow."""

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            google_api_key=settings.google_api_key,
            model=settings.gemini_model,
            temperature=0.1,
            convert_system_message_to_human=True
        )
        self.repo_service = RepositoryService()
        self.excel_service = ExcelService()
        self.review_chain = ReviewChain(self.llm)
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """Create the review workflow graph."""
        workflow = StateGraph(ReviewState)
        workflow.add_node("get_code", self._get_student_code)
        workflow.add_node("analyze_code", self._analyze_code)
        workflow.add_node("review_code", self._review_code)
        workflow.add_node("save_results", self._save_results)
        workflow.add_node("handle_error", self._handle_error)

        workflow.set_entry_point("get_code")
        workflow.add_conditional_edges(
            "get_code",
            lambda state: "handle_error" if state.get("error_message") else "analyze_code",
        )
        workflow.add_edge("analyze_code", "review_code")
        workflow.add_edge("review_code", "save_results")
        workflow.add_edge("save_results", END)
        workflow.add_edge("handle_error", END)
        return workflow.compile()

    def _get_student_code(self, state: ReviewState) -> ReviewState:
        try:
            repo_path = self.repo_service.get_homework_from_github(
                state["username"], state["lecture_number"]
            )
            # Find all task folders in the cloned repo
            tasks = [d for d in repo_path.iterdir() if d.is_dir() and d.name.startswith("task_")]
            
            all_code = {}
            for task_path in tasks:
                task_code = self.repo_service.read_code_from_path(task_path)
                for fname, code in task_code.items():
                    all_code[f"{task_path.name}/{fname}"] = code

            if not all_code:
                state["error_message"] = f"No code found for student {state['username']}"
            else:
                state["code_content"] = all_code
            return state
        except Exception as e:
            state["error_message"] = f"Error retrieving code: {str(e)}"
            return state

    def _analyze_code(self, state: ReviewState) -> ReviewState:
        from ..services import CodeAnalysisService
        analysis_service = CodeAnalysisService()
        code_metrics = analysis_service.get_code_summary(state["code_content"])
        state["code_metrics"] = code_metrics
        return state

    def _review_code(self, state: ReviewState) -> ReviewState:
        tasks_with_code = defaultdict(dict)
        for file_path, content in state["code_content"].items():
            task_name = file_path.split('/')[0]
            tasks_with_code[task_name][file_path] = content

        review_results = []
        for task_name, task_code in tasks_with_code.items():
            task_result = self.review_chain.review_student_task(
                state["username"], state["lecture_number"], task_name, task_code
            )
            review_results.append(task_result)

        avg_score = sum(r.get('score', 0) for r in review_results) / len(review_results) if review_results else 0
        state["review_result"] = {"average_score": avg_score, "task_results": review_results}
        return state

    def _save_results(self, state: ReviewState) -> ReviewState:
        review_result = state["review_result"]
        task_reviews = []
        for task_res in review_result.get("task_results", []):
            task_reviews.append(TaskReview(
                task=task_res.get("task", "unknown"),
                score=int(round(task_res.get("score", 0))),
                comments=task_res.get("comments", ""),
                technical_correctness=int(round(task_res.get("technical_correctness", 0))),
                code_style=int(round(task_res.get("code_style", 0))),
                documentation=int(round(task_res.get("documentation", 0))),
                performance=int(round(task_res.get("performance", 0)))
            ))
        
        response = ReviewResponse(
            username=state["username"],
            lecture_number=state["lecture_number"],
            average_score=review_result.get("average_score", 0),
            total_tasks=len(task_reviews),
            details=task_reviews
        )
        self.excel_service.update_student_review(state["lecture_number"], response)
        state["final_response"] = response
        return state

    def _handle_error(self, state: ReviewState) -> ReviewState:
        error_message = state.get("error_message", "Unknown error")
        logger.error(f"Workflow error: {error_message}")
        state["final_response"] = ReviewResponse(
            username=state["username"],
            lecture_number=state["lecture_number"],
            average_score=0,
            total_tasks=0,
            details=[]
        )
        return state

    async def review_student(self, username: str, lecture_number: int) -> ReviewResponse:
        initial_state = ReviewState(
            username=username,
            lecture_number=lecture_number,
            task=None,
            current_step="start",
            error_message=None,
            code_content={},
            code_metrics={},
            review_result=None,
            final_response=None
        )
        result = await self.workflow.ainvoke(initial_state)
        return result["final_response"]