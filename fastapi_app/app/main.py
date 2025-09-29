"""
FastAPI main application entrypoint.
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager
import time
from datetime import datetime

from .core import logger, settings
# This is the crucial import for your API endpoints
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
    # Service initialization is now handled by dependency injection,
    # so we don't need to do it here.
    yield
    logger.info("Shutting down AI Homework Reviewer application...")

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered homework reviewing system.",
    lifespan=lifespan
)

# --- THIS IS THE CRITICAL LINE THAT WAS MISSING ---
# It tells the main app to include all the GET and POST
# endpoints defined in the review_router.
app.include_router(
    review_router,
    prefix="/api/v1",
    tags=["Review"]
)
# ---------------------------------------------------

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
        "docs": "/docs"
    }

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
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )