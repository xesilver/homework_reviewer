"""
FastAPI endpoints for homework review API.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from datetime import datetime

from ..core import logger, settings
from ..models.schemas import (
    ReviewRequest,
    ReviewResponse,
    LectureReviewRequest,
    LectureReviewResponse,
    HealthResponse
)
from ..agents import HomeworkReviewAgent, LectureReviewAgent
from ..services import RepositoryService, ExcelService


# Create router
router = APIRouter()

# Initialize services
repo_service = RepositoryService()
excel_service = ExcelService()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
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

        # Add processing time to the response
        if result:
            result.processing_time = (end_time - start_time).total_seconds()

        logger.info(f"Completed GitHub review for {request.username} in {result.processing_time:.2f}s")
        return result

    except Exception as e:
        logger.error(f"Error reviewing GitHub student {request.username}: {e}")
        raise HTTPException(status_code=500, detail=f"GitHub review failed: {str(e)}")


@router.post("/review/lecture", response_model=LectureReviewResponse)
async def review_lecture(request: LectureReviewRequest, background_tasks: BackgroundTasks):
    """
    Review all students' submissions for a specific lecture from their GitHub repos.
    """
    try:
        logger.info(f"Starting lecture review for lecture {request.lecture_number}")

        # The logic to get usernames would need to come from a pre-defined list or another service,
        # as we no longer scan a local directory. For now, it relies on the request.
        usernames = request.usernames
        if not usernames:
            raise HTTPException(
                status_code=400,
                detail="A list of usernames is required for a lecture review."
            )

        lecture_agent = LectureReviewAgent()

        start_time = datetime.now()
        # This part of the agent would need to be adapted to iterate through usernames
        # For now, this is a placeholder for the logic.
        # result = await lecture_agent.review_lecture(request.lecture_number, usernames)
        # The agent logic should be updated to handle this, for now, we simulate.
        student_results = []
        review_agent = HomeworkReviewAgent()
        for username in usernames:
             student_results.append(await review_agent.review_student(username, request.lecture_number))
        
        end_time = datetime.now()

        total_students = len(student_results)
        average_score = sum(res.average_score for res in student_results) / total_students if total_students > 0 else 0

        response = LectureReviewResponse(
            lecture_number=request.lecture_number,
            total_students=total_students,
            average_score=average_score,
            student_results=student_results,
            processing_time=(end_time - start_time).total_seconds()
        )

        logger.info(f"Completed lecture review for lecture {request.lecture_number}")
        return response

    except Exception as e:
        logger.error(f"Error reviewing lecture {request.lecture_number}: {e}")
        raise HTTPException(status_code=500, detail=f"Lecture review failed: {str(e)}")


# The following endpoints for local file discovery are no longer relevant
# and can be removed or adapted. For now, they are left but may not be useful.

@router.get("/students/{lecture_number}")
async def get_local_students(lecture_number: int):
    """
    (Legacy) Get all students from the local homework directory.
    """
    students = repo_service.get_all_students_in_lecture(lecture_number)
    return {
        "lecture_number": lecture_number,
        "students": students,
        "total_count": len(students),
        "note": "This endpoint reflects the local 'homework' directory, not GitHub users."
    }

@router.get("/tasks/{lecture_number}")
async def get_tasks(lecture_number: int):
    """
    Get all tasks for a specific lecture from the local directory structure.
    """
    tasks = repo_service.get_lecture_tasks(lecture_number)
    return {
        "lecture_number": lecture_number,
        "tasks": tasks,
        "total_count": len(tasks),
        "note": "This endpoint reflects the local 'homework' directory structure."
    }

@router.get("/results/{lecture_number}")
async def get_results(lecture_number: int, student_surname: Optional[str] = None):
    """
    Get review results for a specific lecture.
    
    Args:
        lecture_number: Lecture number
        student_surname: Optional student surname to filter by
        
    Returns:
        Review results
    """
    try:
        results_df = excel_service.get_student_reviews(lecture_number, student_surname)
        
        if results_df.empty:
            return {
                "lecture_number": lecture_number,
                "student_surname": student_surname,
                "results": [],
                "message": "No results found"
            }
        
        # Convert DataFrame to list of dictionaries
        results = results_df.to_dict('records')
        
        return {
            "lecture_number": lecture_number,
            "student_surname": student_surname,
            "results": results,
            "total_count": len(results)
        }
    except Exception as e:
        logger.error(f"Error getting results for lecture {lecture_number}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")


@router.get("/summary/{lecture_number}")
async def get_lecture_summary(lecture_number: int):
    """
    Get summary statistics for a specific lecture.
    
    Args:
        lecture_number: Lecture number
        
    Returns:
        Lecture summary statistics
    """
    try:
        summary = excel_service.get_lecture_summary(lecture_number)
        return {
            "lecture_number": lecture_number,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error getting summary for lecture {lecture_number}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


@router.get("/export/{lecture_number}")
async def export_results(lecture_number: int, format: str = "excel"):
    """
    Export review results for a specific lecture.
    
    Args:
        lecture_number: Lecture number
        format: Export format ("excel" or "csv")
        
    Returns:
        File download response
    """
    try:
        if format.lower() == "excel":
            file_path = excel_service.get_excel_file_path(lecture_number)
            if not file_path.exists():
                raise HTTPException(
                    status_code=404, 
                    detail=f"No Excel file found for lecture {lecture_number}"
                )
            return FileResponse(
                path=str(file_path),
                filename=f"lecture_{lecture_number}_reviews.xlsx",
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        elif format.lower() == "csv":
            csv_path = excel_service.export_to_csv(lecture_number)
            return FileResponse(
                path=str(csv_path),
                filename=f"lecture_{lecture_number}_reviews.csv",
                media_type="text/csv"
            )
        
        else:
            raise HTTPException(
                status_code=400, 
                detail="Invalid format. Use 'excel' or 'csv'"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting results for lecture {lecture_number}: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/validate")
async def validate_repository():
    """
    Validate the homework repository structure.
    
    Returns:
        Validation results
    """
    try:
        validation_issues = repo_service.validate_repository_structure()
        
        is_valid = not any(validation_issues.values())
        
        return {
            "is_valid": is_valid,
            "issues": validation_issues,
            "message": "Repository is valid" if is_valid else "Repository has issues"
        }
    except Exception as e:
        logger.error(f"Error validating repository: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.post("/setup/sample/{lecture_number}")
async def create_sample_structure(lecture_number: int, task_count: int = 2):
    """
    Create sample repository structure for testing.
    
    Args:
        lecture_number: Lecture number
        task_count: Number of tasks to create
        
    Returns:
        Success message
    """
    try:
        repo_service.create_sample_structure(lecture_number, task_count)
        return {
            "message": f"Sample structure created for lecture {lecture_number}",
            "lecture_number": lecture_number,
            "task_count": task_count
        }
    except Exception as e:
        logger.error(f"Error creating sample structure: {e}")
        raise HTTPException(status_code=500, detail=f"Sample creation failed: {str(e)}")


@router.post("/cleanup/{lecture_number}")
async def cleanup_duplicates(lecture_number: int):
    """
    Remove duplicate entries from Excel file, keeping the most recent review for each student-task combination.
    
    Args:
        lecture_number: Lecture number
        
    Returns:
        Success message
    """
    try:
        excel_service.remove_duplicate_entries(lecture_number)
        return {
            "message": f"Duplicate entries removed for lecture {lecture_number}",
            "lecture_number": lecture_number
        }
    except Exception as e:
        logger.error(f"Error cleaning up duplicates: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")