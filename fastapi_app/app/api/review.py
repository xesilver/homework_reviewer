"""
FastAPI endpoints for homework review API.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime

from ..core import logger
from ..models.schemas import (
    ReviewRequest,
    ReviewResponse,
    HealthResponse
)
# The unused LectureReviewAgent is now removed from the import
from ..agents import HomeworkReviewAgent
from ..services import RepositoryService, ExcelService


# Create router
router = APIRouter()

# --- Dependency Injection Functions ---
def get_repo_service() -> RepositoryService:
    return RepositoryService()

def get_excel_service() -> ExcelService:
    return ExcelService()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


@router.post("/review/student", response_model=ReviewResponse)
async def review_student(request: ReviewRequest):
    """
    Review a specific student's homework submission from their GitHub repository.
    """
    try:
        logger.info(f"Starting GitHub review for user {request.username}, lecture {request.lecture_number}")

        review_agent = HomeworkReviewAgent()

        start_time = datetime.now()
        result = await review_agent.review_student(
            username=request.username,
            lecture_number=request.lecture_number
        )
        end_time = datetime.now()

        if result:
            result.processing_time = (end_time - start_time).total_seconds()

        logger.info(f"Completed GitHub review for {request.username} in {result.processing_time:.2f}s")
        return result

    except Exception as e:
        logger.error(f"Error reviewing GitHub student {request.username}: {e}")
        raise HTTPException(status_code=500, detail=f"GitHub review failed: {str(e)}")


@router.get("/results/{lecture_number}")
async def get_results(
    lecture_number: int,
    student_surname: Optional[str] = None,
    excel_service: ExcelService = Depends(get_excel_service)
):
    """
    Get review results for a specific lecture.
    """
    try:
        results_df = excel_service.get_student_reviews(lecture_number, student_surname)
        
        if results_df.empty:
            return {"message": "No results found"}
        
        return results_df.to_dict('records')
        
    except Exception as e:
        logger.error(f"Error getting results for lecture {lecture_number}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")