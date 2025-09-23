import os
import json
import asyncio
from datetime import datetime

# The 'setup.py' file makes this standard import possible.
from fastapi_app.app.agents import HomeworkReviewAgent
from fastapi_app.app.services.notification import NotificationService

# --- Configuration ---
# The list of students to review is now loaded from a JSON file on the EFS volume.
# Default path: /mnt/efs/config/students.json

def load_students_from_config_file():
    """Loads and parses the student configuration from a JSON file on EFS."""
    # The STORAGE_PATH will be /mnt/efs in the Lambda environment
    storage_path = os.environ.get("STORAGE_PATH", "/tmp") # Default to /tmp for local testing
    config_file_path = os.path.join(storage_path, "config", "students.json")
    
    print(f"Attempting to load student configuration from: {config_file_path}")

    if not os.path.exists(config_file_path):
        print(f"WARNING: Configuration file not found at {config_file_path}. Using empty list.")
        return []
    
    try:
        with open(config_file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"ERROR: Could not decode JSON from {config_file_path}. Please check the format.")
        return []
    except Exception as e:
        print(f"ERROR: An unexpected error occurred while reading the config file: {e}")
        return []

def handler(event, context):
    """
    AWS Lambda handler function triggered by a weekly EventBridge schedule.
    """
    print("--- Starting Weekly Homework Review Process ---")

    review_agent = HomeworkReviewAgent()
    notification_service = NotificationService()
    
    students_to_review = load_students_from_config_file()
    review_outcomes = []

    if not students_to_review:
        print("No students configured for review. Exiting.")
        return {'statusCode': 200, 'body': json.dumps('No students to review.')}

    for student in students_to_review:
        username = student.get('username')
        lecture = student.get('lecture')

        if not username or not lecture:
            print(f"Skipping invalid student entry: {student}")
            continue

        print(f"-> Processing student: {username}, lecture: {lecture}")
        
        try:
            result = asyncio.run(review_agent.review_student(
                username=username,
                lecture_number=lecture
            ))
            outcome = f"✅ SUCCESS: {username} - Avg Score: {result.average_score:.2f}"
            print(f"   {outcome}")
            review_outcomes.append(outcome)
        except Exception as e:
            outcome = f"❌ ERROR: Failed to review {username}. Reason: {e}"
            print(f"   {outcome}")
            review_outcomes.append(outcome)

    print("--- Review Process Finished. Sending Email Summary. ---")
    
    recipient = os.environ.get("RECIPIENT_EMAIL")
    if recipient:
        subject = f"Weekly AI Homework Review Summary - {datetime.now().strftime('%Y-%m-%d')}"
        
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
                <p>The updated Excel file is available in the EFS storage mounted at {os.environ.get('STORAGE_PATH', '/mnt/efs')}.</p>
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
