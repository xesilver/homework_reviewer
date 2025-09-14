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
    try:
        return HealthResponse(
            status="healthy",
            version=settings.app_version,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@router.post("/review/student", response_model=ReviewResponse)
async def review_student(request: ReviewRequest):
    """
    Review a specific student's homework submission.
    
    Args:
        request: Review request with student surname and lecture number
        
    Returns:
        ReviewResponse with detailed results
    """
    try:
        logger.info(f"Starting review for student {request.surname}, lecture {request.lecture_number}")
        
        # Validate repository structure
        validation_issues = repo_service.validate_repository_structure()
        if validation_issues.get("missing_directories") or validation_issues.get("no_students"):
            raise HTTPException(
                status_code=400, 
                detail=f"Repository validation failed: {validation_issues}"
            )
        
        # Create review agent
        review_agent = HomeworkReviewAgent()
        
        # Perform review
        start_time = datetime.now()
        result = await review_agent.review_student(
            request.surname,
            request.lecture_number
        )
        end_time = datetime.now()
        
        # Add processing time
        processing_time = (end_time - start_time).total_seconds()
        result.processing_time = processing_time
        
        logger.info(f"Completed review for {request.surname} in {processing_time:.2f}s")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reviewing student {request.surname}: {e}")
        raise HTTPException(status_code=500, detail=f"Review failed: {str(e)}")


@router.post("/review/lecture", response_model=LectureReviewResponse)
async def review_lecture(request: LectureReviewRequest, background_tasks: BackgroundTasks):
    """
    Review all students' submissions for a specific lecture.
    
    Args:
        request: Lecture review request
        background_tasks: FastAPI background tasks
        
    Returns:
        LectureReviewResponse with results
    """
    try:
        logger.info(f"Starting lecture review for lecture {request.lecture_number}")
        
        # Validate repository structure
        validation_issues = repo_service.validate_repository_structure()
        if validation_issues.get("missing_directories") or validation_issues.get("no_students"):
            raise HTTPException(
                status_code=400, 
                detail=f"Repository validation failed: {validation_issues}"
            )
        
        # Get students to review
        if request.students:
            students = request.students
        else:
            students = repo_service.get_all_students_in_lecture(request.lecture_number)
        
        if not students:
            raise HTTPException(
                status_code=404, 
                detail=f"No students found for lecture {request.lecture_number}"
            )
        
        # Create lecture review agent
        lecture_agent = LectureReviewAgent()
        
        # Perform review
        start_time = datetime.now()
        result = await lecture_agent.review_lecture(
            request.lecture_number,
            students
        )
        end_time = datetime.now()
        
        # Calculate summary statistics
        student_results = result.get("student_results", [])
        total_students = len(student_results)
        
        if total_students > 0:
            # Calculate average score
            total_score = 0
            valid_results = 0
            
            for student_result in student_results:
                if student_result:  # Check if result exists
                    total_score += student_result.average_score
                    valid_results += 1
            
            average_score = total_score / valid_results if valid_results > 0 else 0
        else:
            average_score = 0
        
        # Create response
        response = LectureReviewResponse(
            lecture_number=request.lecture_number,
            total_students=total_students,
            average_score=average_score,
            student_results=[sr for sr in student_results if sr],  # Filter out None results
            processing_time=(end_time - start_time).total_seconds()
        )
        
        logger.info(f"Completed lecture review for lecture {request.lecture_number}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reviewing lecture {request.lecture_number}: {e}")
        raise HTTPException(status_code=500, detail=f"Lecture review failed: {str(e)}")


@router.get("/students/{lecture_number}")
async def get_students(lecture_number: int):
    """
    Get all students who have submissions for a specific lecture.
    
    Args:
        lecture_number: Lecture number
        
    Returns:
        List of student surnames
    """
    try:
        students = repo_service.get_all_students_in_lecture(lecture_number)
        return {
            "lecture_number": lecture_number,
            "students": students,
            "total_count": len(students)
        }
    except Exception as e:
        logger.error(f"Error getting students for lecture {lecture_number}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get students: {str(e)}")


@router.get("/tasks/{lecture_number}")
async def get_tasks(lecture_number: int):
    """
    Get all tasks for a specific lecture.
    
    Args:
        lecture_number: Lecture number
        
    Returns:
        List of task identifiers
    """
    try:
        tasks = repo_service.get_lecture_tasks(lecture_number)
        return {
            "lecture_number": lecture_number,
            "tasks": tasks,
            "total_count": len(tasks)
        }
    except Exception as e:
        logger.error(f"Error getting tasks for lecture {lecture_number}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tasks: {str(e)}")


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
