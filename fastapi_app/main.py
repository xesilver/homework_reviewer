import os
import json
import asyncio
from datetime import datetime
from google.cloud import storage

# The 'setup.py' file makes this standard import possible.
from fastapi_app.app.agents import HomeworkReviewAgent
from fastapi_app.app.services.notification import NotificationService
from fastapi_app.app.services.repository_service import RepositoryService


def load_students_from_gcs():
    """Loads and parses the student configuration from a JSON file in GCS."""
    bucket_name = os.environ.get("GCS_BUCKET_NAME")
    config_file_path = "config/students.json"
    
    if not bucket_name:
        print("ERROR: GCS_BUCKET_NAME not set. Cannot load student config.")
        return []

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(config_file_path)
        
        print(f"Attempting to load student configuration from: gs://{bucket_name}/{config_file_path}")
        
        if not blob.exists():
            print(f"WARNING: Configuration file not found at gs://{bucket_name}/{config_file_path}.")
            return []
            
        config_content = blob.download_as_text()
        return json.loads(config_content)
    except Exception as e:
        print(f"ERROR: An unexpected error occurred while reading the config file from GCS: {e}")
        return []

def homework_review_triggered(event, context):
    """
    Google Cloud Function triggered by Cloud Scheduler.
    """
    print("--- Starting Weekly Homework Review Process ---")

    review_agent = HomeworkReviewAgent()
    repo_service = RepositoryService()
    notification_service = NotificationService()
    
    students_to_review = load_students_from_gcs()
    review_outcomes = []

    if not students_to_review:
        print("No students configured for review. Exiting.")
        return ('No students to review.', 200)

    for student in students_to_review:
        username = student.get('username')
        lecture = student.get('lecture')
        repo_path = None # To store the path for cleanup

        if not username or not lecture:
            print(f"Skipping invalid student entry: {student}")
            continue

        print(f"-> Processing student: {username}, lecture: {lecture}")
        
        try:
            # The agent now uses the updated repo_service which clones to /tmp
            result = asyncio.run(review_agent.review_student(
                username=username,
                lecture_number=lecture
            ))
            # Get the path for cleanup
            repo_path = repo_service.github_repos_path / username / f"lecture_{lecture}"

            outcome = f"✅ SUCCESS: {username} - Avg Score: {result.average_score:.2f}"
            print(f"   {outcome}")
            review_outcomes.append(outcome)
        except Exception as e:
            outcome = f"❌ ERROR: Failed to review {username}. Reason: {e}"
            print(f"   {outcome}")
            review_outcomes.append(outcome)
        finally:
            # Ensure cleanup happens whether the review succeeds or fails
            if repo_path:
                repo_service.cleanup_repository(repo_path)

    print("--- Review Process Finished. Sending Email Summary. ---")
    
    recipient = os.environ.get("RECIPIENT_EMAIL")
    if recipient:
        subject = f"Weekly AI Homework Review Summary - {datetime.now().strftime('%Y-%m-%d')}"
        
        outcomes_html = "".join([f"<li>{outcome}</li>" for outcome in review_outcomes])
        body_html = f"""
        <html>
            <body>
                <h1>AI Homework Review Report</h1>
                <p>The weekly automated review process has completed. Here are the results:</p>
                <ul>
                    {outcomes_html}
                </ul>
                <p>The updated Excel reports are available in the GCS bucket: {os.environ.get('GCS_BUCKET_NAME')}.</p>
            </body>
        </html>
        """
        notification_service.send_summary_email(
            recipient_email=recipient,
            subject=subject,
            body_html=body_html
        )

    return ('Weekly review process completed successfully!', 200)