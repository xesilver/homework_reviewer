"""
FastAPI main application entrypoint.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager
import time
from datetime import datetime

from .core import logger, settings
from .api import review_router
from .models.schemas import ErrorResponse


# Global variable to track startup time
startup_time = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global startup_time
    startup_time = time.time()
    logger.info("Starting AI Homework Reviewer application...")
    
    # Initialize services
    try:
        from .services import RepositoryService, ExcelService
        
        # Ensure directories exist
        repo_service = RepositoryService()
        excel_service = ExcelService()
        
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    
    yield
    
    logger.info("Shutting down AI Homework Reviewer application...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    AI-powered homework reviewing system built with FastAPI, LangChain, and LangGraph.
    
    This system automates the process of checking students' homework submissions, 
    evaluates them based on technical requirements, code style, and other quality metrics, 
    and stores the results in Excel files mapped to each student.
    
    ## Features
    
    * **Automated Review**: Uses AI to evaluate code submissions
    * **Multiple Criteria**: Technical correctness, code style, documentation, performance
    * **Excel Integration**: Results stored in structured Excel files
    * **Batch Processing**: Review entire lectures or individual students
    * **RESTful API**: Easy integration with other systems
    
    ## Quick Start
    
    1. Set up your OpenAI API key in environment variables
    2. Organize homework submissions in the `homework/` directory
    3. Use the `/review/student` endpoint to review individual submissions
    4. Use the `/review/lecture` endpoint to review entire lectures
    5. Export results using the `/export/{lecture_number}` endpoint
    """,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    review_router,
    prefix="/api/v1",
    tags=["Review"]
)


@app.get("/", response_class=JSONResponse)
async def root():
    """Root endpoint with API information."""
    uptime = time.time() - startup_time if startup_time else 0
    
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "uptime_seconds": uptime,
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "review_student": "/api/v1/review/student",
            "review_lecture": "/api/v1/review/lecture",
            "get_students": "/api/v1/students/{lecture_number}",
            "get_tasks": "/api/v1/tasks/{lecture_number}",
            "get_results": "/api/v1/results/{lecture_number}",
            "export_results": "/api/v1/export/{lecture_number}",
            "validate_repository": "/api/v1/validate",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/health", response_class=JSONResponse)
async def health_check():
    """Health check endpoint."""
    try:
        uptime = time.time() - startup_time if startup_time else 0
        
        return {
            "status": "healthy",
            "version": settings.app_version,
            "uptime_seconds": uptime,
            "timestamp": datetime.now().isoformat(),
            "services": {
                "repository": "ok",
                "excel": "ok",
                "ai_review": "ok" if settings.openai_api_key else "not_configured"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            timestamp=datetime.now().isoformat()
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc),
            timestamp=datetime.now().isoformat()
        ).dict()
    )


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
