"""
Agents module initialization.
"""
from .simple_review_agent import SimpleReviewAgent as HomeworkReviewAgent, SimpleLectureReviewAgent as LectureReviewAgent

__all__ = [
    "HomeworkReviewAgent",
    "LectureReviewAgent",
]
