import os
import json
import asyncio
from datetime import datetime
from google.cloud import storage

# It's good practice to import all necessary modules at the top
try:
    print("Importing application modules...")
    from fastapi_app.app.agents import HomeworkReviewAgent
    from fastapi_app.app.services.notification import NotificationService
    from fastapi_app.app.services.repository_service import RepositoryService
    print("Application modules imported successfully.")
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
        print("Exiting function due to an error in loading student configuration.")
        return ('Failed to load configuration.', 500)

    if not students_to_review:
        print("No students configured for review. Exiting.")
        return ('No students to review.', 200)

    print(f"Successfully loaded {len(students_to_review)} students for review.")
    
    try:
        print("Initializing HomeworkReviewAgent...")
        review_agent = HomeworkReviewAgent()
        print("HomeworkReviewAgent initialized successfully.")

        print("Initializing RepositoryService...")
        repo_service = RepositoryService()
        print("RepositoryService initialized successfully.")
        
        review_outcomes = []

    except Exception as e:
        print(f"CRITICAL ERROR during service initialization: {e}")
        return ('Failed to initialize services.', 500)


    for student in students_to_review:
        username = student.get('username')
        lecture = student.get('lecture')
        repo_path = None

        if not username or not lecture:
            print(f"Skipping invalid student entry: {student}")
            continue

        print(f"-> Processing student: {username}, lecture: {lecture}")
        
        try:
            result = asyncio.run(review_agent.review_student(
                username=username,
                lecture_number=lecture
            ))
            repo_path = repo_service.github_repos_path / username / f"lecture_{lecture}"
            outcome = f"✅ SUCCESS: {username} - Avg Score: {result.average_score:.2f}"
            print(f"   {outcome}")
            review_outcomes.append(outcome)
        except Exception as e:
            outcome = f"❌ ERROR: Failed to review {username}. Reason: {e}"
            print(f"   {outcome}")
            review_outcomes.append(outcome)
        finally:
            if repo_path:
                repo_service.cleanup_repository(repo_path)

    print("--- Review Process Finished. ---")
    
    return ('Weekly review process completed successfully!', 200)