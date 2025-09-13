"""
LangChain prompt templates for homework review.
"""
from typing import Dict, List, Any
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser
from pydantic import BaseModel, Field


class ReviewCriteria(BaseModel):
    """Model for review criteria."""
    technical_correctness: int = Field(ge=0, le=100, description="Technical correctness score (0-100)")
    code_style: int = Field(ge=0, le=100, description="Code style score (0-100)")
    documentation: int = Field(ge=0, le=100, description="Documentation score (0-100)")
    performance: int = Field(ge=0, le=100, description="Performance score (0-100)")
    overall_score: int = Field(ge=0, le=100, description="Overall score (0-100)")
    comments: str = Field(description="Detailed review comments")


class ReviewOutputParser(BaseOutputParser[ReviewCriteria]):
    """Parser for review output."""
    
    def parse(self, text: str) -> ReviewCriteria:
        """Parse the review output into structured format."""
        # This is a simplified parser - in practice, you'd want more robust parsing
        lines = text.strip().split('\n')
        
        # Extract scores (simplified approach)
        technical_correctness = 80  # Default values
        code_style = 80
        documentation = 80
        performance = 80
        overall_score = 80
        comments = "Review completed"
        
        # Try to extract scores from text
        for line in lines:
            if "technical" in line.lower() and ":" in line:
                try:
                    technical_correctness = int(line.split(":")[-1].strip())
                except:
                    pass
            elif "style" in line.lower() and ":" in line:
                try:
                    code_style = int(line.split(":")[-1].strip())
                except:
                    pass
            elif "documentation" in line.lower() and ":" in line:
                try:
                    documentation = int(line.split(":")[-1].strip())
                except:
                    pass
            elif "performance" in line.lower() and ":" in line:
                try:
                    performance = int(line.split(":")[-1].strip())
                except:
                    pass
            elif "overall" in line.lower() and ":" in line:
                try:
                    overall_score = int(line.split(":")[-1].strip())
                except:
                    pass
        
        # Extract comments (everything after "Comments:" or similar)
        comment_start = -1
        for i, line in enumerate(lines):
            if "comment" in line.lower() and ":" in line:
                comment_start = i
                break
        
        if comment_start >= 0:
            comments = "\n".join(lines[comment_start:]).split(":", 1)[-1].strip()
        
        return ReviewCriteria(
            technical_correctness=technical_correctness,
            code_style=code_style,
            documentation=documentation,
            performance=performance,
            overall_score=overall_score,
            comments=comments
        )


# Main review prompt template
REVIEW_PROMPT_TEMPLATE = """
You are an expert code reviewer tasked with evaluating student homework submissions. 
Your role is to provide constructive feedback and accurate scoring based on multiple criteria.

**Task Information:**
- Student: {student_surname}
- Lecture: {lecture_number}
- Task: {task_name}
- Task Description: {task_description}

**Code to Review:**
{code_content}

**Code Metrics:**
{code_metrics}

**Review Criteria:**

1. **Technical Correctness (40% weight)**
   - Does the code work correctly?
   - Are there any bugs or logical errors?
   - Does it meet the specified requirements?
   - Are edge cases handled properly?

2. **Code Style & Readability (30% weight)**
   - Is the code clean and readable?
   - Are variable and function names descriptive?
   - Is the code properly formatted and indented?
   - Are there appropriate comments?

3. **Documentation (20% weight)**
   - Are there docstrings for functions/classes?
   - Is the code self-documenting?
   - Are there README files or comments explaining the approach?

4. **Performance (10% weight)**
   - Is the code efficient?
   - Are there any obvious performance issues?
   - Is the algorithm choice appropriate?

**Scoring Guidelines:**
- 90-100: Excellent - Exceeds expectations
- 80-89: Good - Meets expectations with minor issues
- 70-79: Satisfactory - Meets basic requirements
- 60-69: Needs improvement - Has significant issues
- 0-59: Poor - Does not meet requirements

**Output Format:**
Please provide your review in the following format:

Technical Correctness: [score 0-100]
Code Style: [score 0-100]
Documentation: [score 0-100]
Performance: [score 0-100]
Overall Score: [score 0-100]

Comments:
[Detailed feedback explaining the scores and providing specific suggestions for improvement]

Remember to be constructive and educational in your feedback. Focus on helping the student learn and improve.
"""

# Create the prompt template
review_prompt = PromptTemplate(
    input_variables=[
        "student_surname",
        "lecture_number", 
        "task_name",
        "task_description",
        "code_content",
        "code_metrics"
    ],
    template=REVIEW_PROMPT_TEMPLATE
)

# Simplified review prompt for quick reviews
QUICK_REVIEW_PROMPT_TEMPLATE = """
Review this code submission and provide a score (0-100) and brief comments.

Student: {student_surname}
Task: {task_name}
Code: {code_content}

Provide:
Score: [0-100]
Comments: [Brief feedback]
"""

quick_review_prompt = PromptTemplate(
    input_variables=["student_surname", "task_name", "code_content"],
    template=QUICK_REVIEW_PROMPT_TEMPLATE
)

# Code analysis prompt
CODE_ANALYSIS_PROMPT_TEMPLATE = """
Analyze the following code and provide insights about:

1. Code quality metrics
2. Potential issues or bugs
3. Performance considerations
4. Style and readability
5. Documentation quality

Code:
{code_content}

Provide a structured analysis focusing on these areas.
"""

code_analysis_prompt = PromptTemplate(
    input_variables=["code_content"],
    template=CODE_ANALYSIS_PROMPT_TEMPLATE
)

# Task-specific prompts
TASK_SPECIFIC_PROMPT_TEMPLATE = """
You are reviewing a specific programming task. Here are the task requirements:

**Task Requirements:**
{task_requirements}

**Student Submission:**
{code_content}

**Code Metrics:**
{code_metrics}

Evaluate the submission against the specific requirements and provide:
1. Technical correctness score (0-100)
2. Code style score (0-100) 
3. Documentation score (0-100)
4. Performance score (0-100)
5. Overall score (0-100)
6. Detailed comments explaining your evaluation

Focus on how well the submission meets the specific task requirements.
"""

task_specific_prompt = PromptTemplate(
    input_variables=["task_requirements", "code_content", "code_metrics"],
    template=TASK_SPECIFIC_PROMPT_TEMPLATE
)

# Batch review prompt for multiple students
BATCH_REVIEW_PROMPT_TEMPLATE = """
You are reviewing multiple student submissions for the same task. Provide consistent scoring across all submissions.

**Task:** {task_name}
**Task Description:** {task_description}

**Submissions:**
{submissions}

For each submission, provide:
- Student: [surname]
- Score: [0-100]
- Comments: [Brief feedback]

Ensure scoring is consistent and fair across all submissions.
"""

batch_review_prompt = PromptTemplate(
    input_variables=["task_name", "task_description", "submissions"],
    template=BATCH_REVIEW_PROMPT_TEMPLATE
)

# Summary prompt for lecture-wide reviews
LECTURE_SUMMARY_PROMPT_TEMPLATE = """
Provide a summary of the lecture review results:

**Lecture:** {lecture_number}
**Total Students:** {total_students}
**Average Score:** {average_score}

**Student Results:**
{student_results}

**Key Insights:**
- Common issues across submissions
- Areas where students excelled
- Recommendations for future lectures

Provide a comprehensive summary suitable for instructor review.
"""

lecture_summary_prompt = PromptTemplate(
    input_variables=[
        "lecture_number",
        "total_students", 
        "average_score",
        "student_results"
    ],
    template=LECTURE_SUMMARY_PROMPT_TEMPLATE
)
