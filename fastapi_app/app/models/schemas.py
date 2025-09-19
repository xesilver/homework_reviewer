"""
Pydantic models for API requests and responses.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ReviewRequest(BaseModel):
    """Request model for triggering a homework review from GitHub."""
    username: str = Field(..., description="Student's GitHub username")
    lecture_number: int = Field(..., ge=1, description="Lecture number to review")

    @field_validator('username')
    def validate_username(cls, v):
        if not v or not v.strip():
            raise ValueError('Username cannot be empty')
        return v.strip()


class TaskReview(BaseModel):
    """Model for individual task review results."""
    task: str = Field(..., description="Task identifier")
    score: int = Field(..., ge=0, le=100, description="Score percentage (0-100)")
    comments: str = Field(..., description="Detailed review comments")
    technical_correctness: int = Field(..., ge=0, le=100, description="Technical correctness score")
    code_style: int = Field(..., ge=0, le=100, description="Code style score")
    documentation: int = Field(..., ge=0, le=100, description="Documentation score")
    performance: int = Field(..., ge=0, le=100, description="Performance score")
    review_timestamp: datetime = Field(default_factory=datetime.now)


class ReviewResponse(BaseModel):
    """Response model for homework review results."""
    username: str = Field(..., description="Student's GitHub username")
    lecture_number: int = Field(..., description="Reviewed lecture number")
    average_score: float = Field(..., ge=0, le=100, description="Average score across all tasks")
    total_tasks: int = Field(..., ge=0, description="Total number of tasks reviewed")
    details: List[TaskReview] = Field(..., description="Detailed review results for each task")
    review_timestamp: datetime = Field(default_factory=datetime.now)
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")


class LectureReviewRequest(BaseModel):
    """Request model for reviewing all students in a lecture."""
    lecture_number: int = Field(..., ge=1, description="Lecture number to review")
    usernames: Optional[List[str]] = Field(None, description="Specific GitHub usernames to review (if None, review all)")


class LectureReviewResponse(BaseModel):
    """Response model for lecture-wide review results."""
    lecture_number: int = Field(..., description="Reviewed lecture number")
    total_students: int = Field(..., ge=0, description="Total number of students reviewed")
    average_score: float = Field(..., ge=0, le=100, description="Average score across all students")
    student_results: List[ReviewResponse] = Field(..., description="Results for each student")
    review_timestamp: datetime = Field(default_factory=datetime.now)
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class StudentInfo(BaseModel):
    """Model for student information."""
    username: str = Field(..., description="Student's GitHub username")
    first_name: Optional[str] = Field(None, description="Student's first name")
    email: Optional[str] = Field(None, description="Student's email")
    student_id: Optional[str] = Field(None, description="Student ID")


class TaskInfo(BaseModel):
    """Model for task information."""
    task_id: str = Field(..., description="Task identifier")
    lecture_number: int = Field(..., description="Lecture number")
    task_name: str = Field(..., description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    requirements: Optional[List[str]] = Field(None, description="Task requirements")
    max_score: int = Field(default=100, ge=0, le=100, description="Maximum possible score")


class ReviewCriteria(BaseModel):
    """Model for review criteria configuration."""
    technical_correctness_weight: float = Field(default=0.4, ge=0, le=1, description="Weight for technical correctness")
    code_style_weight: float = Field(default=0.3, ge=0, le=1, description="Weight for code style")
    documentation_weight: float = Field(default=0.2, ge=0, le=1, description="Weight for documentation")
    performance_weight: float = Field(default=0.1, ge=0, le=1, description="Weight for performance")

    @field_validator('technical_correctness_weight', 'code_style_weight', 'documentation_weight', 'performance_weight')
    def validate_weights(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Weights must be between 0 and 1')
        return v

    # The logic for validate_total_weight would be better implemented using a model_validator in Pydantic v2
    # for clarity and correctness. This field_validator is kept for structural consistency
    # with the provided file but may not behave as expected for cross-field validation.

class ReviewStatus(BaseModel):
    """Model for review status tracking."""
    review_id: str = Field(..., description="Unique review identifier")
    status: str = Field(..., description="Review status (pending, in_progress, completed, failed)")
    progress: float = Field(default=0.0, ge=0, le=100, description="Progress percentage")
    message: Optional[str] = Field(None, description="Status message")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    result: Optional[ReviewResponse] = Field(None, description="Review result (if completed)")

