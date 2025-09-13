"""
Logging configuration for the AI Homework Reviewer.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

from .config import settings


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        format_string: Custom format string
        
    Returns:
        Configured logger instance
    """
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )
    
    # Prepare handlers
    handlers = [logging.StreamHandler(sys.stdout)]
    
    # Add file handler if log_file is provided
    if log_file:
        try:
            # Ensure the log directory exists
            log_file.parent.mkdir(parents=True, exist_ok=True)
            handlers.append(logging.FileHandler(log_file))
        except Exception as e:
            # If file logging fails, just use console logging
            print(f"Warning: Could not set up file logging: {e}")
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        handlers=handlers
    )
    
    # Create logger for the application
    logger = logging.getLogger("homework_reviewer")
    
    # Set specific loggers to appropriate levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("langgraph").setLevel(logging.WARNING)
    
    return logger


# Global logger instance
try:
    logger = setup_logging(
        level="DEBUG" if settings.debug else "INFO",
        log_file=Path("logs") / "homework_reviewer.log" if not settings.debug else None
    )
except Exception as e:
    # Fallback to basic console logging if setup fails
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("homework_reviewer")
    logger.warning(f"Failed to set up advanced logging: {e}")
