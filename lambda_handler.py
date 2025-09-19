# lambda_handler.py
import os
import json
import asyncio
from datetime import datetime
from fastapi_app.app.agents import HomeworkReviewAgent
from fastapi_app.app.services.notification import NotificationService

# --- Configuration ---
# Set these environment variables in your Lambda function configuration:
# STORAGE_PATH: The mount path for your EFS, e.g., /mnt/efs
# GITHUB_TOKEN: Your GitHub personal access token.
# OPENAI_API_KEY: Your OpenAI API key.
# SENDER_EMAIL: The SES-verified email address you're sending from.
# RECIPIENT_EMAIL: The email address to send the summary to.
# AWS_REGION: The AWS region your Lambda and SES are in (e.g., 'us-east-1').

STUDENTS_TO_REVIEW = [
    {"github_nickname": "xesilver", "lecture": 1},
    # Add other students here
]

def handler(event, context):
    """
    AWS Lambda handler function triggered by a weekly EventBridge schedule.
    """
    print("--- Starting Weekly Homework Review Process ---")

    review_agent = HomeworkReviewAgent()
    notification_service = NotificationService()
    
    review_outcomes = []

    for student in STUDENTS_TO_REVIEW:
        nickname = student['github_nickname']
        lecture = student['lecture']
        print(f"-> Processing student: {nickname}, lecture: {lecture}")
        
        try:
            result = asyncio.run(review_agent.review_student(
                student_surname=nickname,
                lecture_number=lecture,
                github_nickname=nickname
            ))
            outcome = f"✅ SUCCESS: {nickname} - Avg Score: {result.average_score:.2f}"
            print(f"   {outcome}")
            review_outcomes.append(outcome)
        except Exception as e:
            outcome = f"❌ ERROR: Failed to review {nickname}. Reason: {e}"
            print(f"   {outcome}")
            review_outcomes.append(outcome)

    print("--- Review Process Finished. Sending Email Summary. ---")
    
    # --- Prepare and Send Email ---
    recipient = os.environ.get("RECIPIENT_EMAIL")
    if recipient:
        subject = f"Weekly AI Homework Review Summary - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Build an HTML body for the email
        outcomes_html = "".join([f"<li>{outcome}</li>" for outcome in review_outcomes])
        body_html = f"""
        <html>
            <head></head>
            <body>
                <h1>AI Homework Review Report</h1>
                <p>The weekly automated review process has completed. Here are the results:</p>
                <ul>
                    {outcomes_html}
                </ul>
                <p>The updated Excel file is available in the EFS storage.</p>
            </body>
        </html>
        """
        
        notification_service.send_summary_email(
            recipient_email=recipient,
            subject=subject,
            body_html=body_html
        )
    else:
        print("WARNING: RECIPIENT_EMAIL not set. Skipping email notification.")

    return {
        'statusCode': 200,
        'body': json.dumps('Weekly review process and email notification completed successfully!')
    }