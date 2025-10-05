import os
import json
import asyncio
from datetime import datetime
from google.cloud import storage

try:
    from fastapi_app.app.agents import HomeworkReviewAgent
    from fastapi_app.app.services.notification import NotificationService
    from fastapi_app.app.services.repository_service import RepositoryService
    from fastapi_app.app.services.excel import ExcelService
    from fastapi_app.app.core.config import settings
except ImportError as e:
    print(f"CRITICAL ERROR: Failed to import application modules: {e}")


def load_students_from_gcs():
    """Loads and parses the student configuration from a JSON file in GCS."""
    bucket_name = os.environ.get("GCS_BUCKET_NAME")
    config_file_path = "config/students.json"

    if not bucket_name:
        print("ERROR: GCS_BUCKET_NAME environment variable not set.")
        return None

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(config_file_path)

        if not blob.exists():
            print(f"ERROR: Configuration file not found at gs://{bucket_name}/{config_file_path}.")
            return None

        config_content = blob.download_as_text()
        students = json.loads(config_content)
        return students

    except Exception as e:
        print(f"CRITICAL ERROR during GCS operation: {e}")
        return None

def homework_review_triggered(request):
    """
    Google Cloud Function triggered by Cloud Scheduler.
    """
    print("--- Starting Weekly Homework Review Process ---")

    students_to_review = load_students_from_gcs()

    if students_to_review is None:
        return ('Failed to load configuration.', 500)
    if not students_to_review:
        return ('No students to review.', 200)

    print(f"Successfully loaded {len(students_to_review)} students for review.")

    try:
        review_agent = HomeworkReviewAgent()
        repo_service = RepositoryService()
        excel_service = ExcelService()
        review_outcomes = []
    except Exception as e:
        print(f"CRITICAL ERROR during service initialization: {e}")
        return ('Failed to initialize services.', 500)

    processed_lectures = set()
    for student in students_to_review:
        username = student.get('username')
        lecture = student.get('lecture')
        repo_path = None
        processed_lectures.add(lecture)

        if not username or not lecture:
            print(f"Skipping invalid student entry: {student}")
            continue

        print(f"-> Processing student: {username}, lecture: {lecture}")

        try:
            result = asyncio.run(review_agent.review_student(username=username, lecture_number=lecture))
            repo_path = repo_service.github_repos_path / username / f"lecture_{lecture}"
            outcome = f"✅ SUCCESS: {username} - Avg Score: {result.average_score:.2f}"
            review_outcomes.append(outcome)
        except Exception as e:
            outcome = f"❌ ERROR: Failed to review {username}. Reason: {e}"
            review_outcomes.append(outcome)
        finally:
            if repo_path:
                repo_service.cleanup_repository(repo_path)

    print("--- Review Process Finished. Preparing email notification. ---")

    if settings.smtp_host and settings.recipient_email:
        notification_service = NotificationService()
        subject = f"Weekly AI Homework Review Summary - {datetime.now().strftime('%Y-%m-%d')}"

        links_html = ""
        for lecture_num in sorted(list(processed_lectures)):
            signed_url = excel_service.get_excel_signed_url(lecture_num)
            if signed_url:
                links_html += f'<li><a href="{signed_url}">Download Report for Lecture {lecture_num}</a> (Link valid for 1 hour)</li>'
            else:
                links_html += f"<li>Could not generate download link for Lecture {lecture_num} report.</li>"

        outcomes_html = "".join([f"<li>{outcome}</li>" for outcome in review_outcomes])
        body_html = f"""
        <html>
            <body>
                <h1>AI Homework Review Report</h1>
                <p>The weekly automated review process has completed. Here are the results:</p>
                <h3>Review Outcomes:</h3>
                <ul>{outcomes_html}</ul>
                <h3>Download Reports:</h3>
                <ul>{links_html}</ul>
            </body>
        </html>
        """
        notification_service.send_summary_email(
            recipient_email=settings.recipient_email,
            subject=subject,
            body_html=body_html
        )
    else:
        print("WARNING: SMTP settings not fully configured. Skipping email notification.")

    return ('Weekly review process completed successfully!', 200)