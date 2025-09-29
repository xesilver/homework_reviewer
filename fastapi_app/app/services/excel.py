import pandas as pd
from pathlib import Path
import io
import os
from typing import Optional
from google.cloud import storage

from ..core import logger
from ..core.config import settings
from ..models.schemas import ReviewResponse


class ExcelService:
    """Service for handling Excel files with review results stored in GCS."""

    def __init__(self, results_dir: Optional[Path] = None):
        self.gcs_client = storage.Client(project=settings.gcp_project_id)
        self.bucket_name = os.environ.get("GCS_BUCKET_NAME")
        self.results_folder = "results"

    def get_excel_blob_path(self, lecture_number: int) -> str:
        """Get the GCS blob path for a specific lecture's Excel file."""
        return f"{self.results_folder}/lecture_{lecture_number}_reviews.xlsx"
        
    def get_student_reviews(self, lecture_number: int, username: Optional[str] = None) -> pd.DataFrame:
        """
        Get review results from Excel file in GCS.
        """
        if not self.bucket_name:
            logger.error("GCS_BUCKET_NAME environment variable not set.")
            return pd.DataFrame()

        bucket = self.gcs_client.bucket(self.bucket_name)
        blob_path = self.get_excel_blob_path(lecture_number)
        blob = bucket.blob(blob_path)
        
        try:
            file_content = blob.download_as_bytes()
            df = pd.read_excel(io.BytesIO(file_content), sheet_name='Reviews')
            if username:
                df = df[df['Username'] == username]
            return df
        except Exception:
            logger.warning(f"Excel file not found in GCS: gs://{self.bucket_name}/{blob_path}")
            return pd.DataFrame()


    def update_student_review(self, lecture_number: int, review_response: ReviewResponse) -> None:
        """
        Update Excel file in GCS with review results for a student.
        """
        if not self.bucket_name:
            logger.error("GCS_BUCKET_NAME environment variable not set. Cannot access GCS.")
            return

        bucket = self.gcs_client.bucket(self.bucket_name)
        blob_path = self.get_excel_blob_path(lecture_number)
        blob = bucket.blob(blob_path)

        try:
            # Download existing file content from GCS
            file_content = blob.download_as_bytes()
            df = pd.read_excel(io.BytesIO(file_content), sheet_name='Reviews')
            logger.info(f"Loaded existing Excel file from GCS: gs://{self.bucket_name}/{blob_path}")
        except Exception:
            # File doesn't exist, create a new DataFrame
            logger.info("Excel file not found in GCS. Creating a new one.")
            df = pd.DataFrame(columns=[
                'Username', 'Lecture', 'Task', 'Score (%)', 'Comments',
                'Technical Correctness', 'Code Style', 'Documentation',
                'Performance', 'Review Date'
            ])
            
        # Update or add new rows
        for task_review in review_response.details:
            mask = (df['Username'] == review_response.username) & (df['Task'].astype(str) == str(task_review.task))

            if mask.any():
                df.loc[mask, 'Score (%)'] = task_review.score
                df.loc[mask, 'Comments'] = task_review.comments
                df.loc[mask, 'Technical Correctness'] = task_review.technical_correctness
                df.loc[mask, 'Code Style'] = task_review.code_style
                df.loc[mask, 'Documentation'] = task_review.documentation
                df.loc[mask, 'Performance'] = task_review.performance
                df.loc[mask, 'Review Date'] = task_review.review_timestamp.strftime('%Y-%m-%d %H:%M:%S')
            else:
                new_row = {
                    'Username': review_response.username,
                    'Lecture': lecture_number,
                    'Task': task_review.task,
                    'Score (%)': task_review.score,
                    'Comments': task_review.comments,
                    'Technical Correctness': task_review.technical_correctness,
                    'Code Style': task_review.code_style,
                    'Documentation': task_review.documentation,
                    'Performance': task_review.performance,
                    'Review Date': task_review.review_timestamp.strftime('%Y-%m-%d %H:%M:%S')
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        # Save updated DataFrame to a byte buffer
        output_buffer = io.BytesIO()
        with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Reviews', index=False)

        # Upload the buffer to GCS
        output_buffer.seek(0)
        blob.upload_from_file(output_buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        logger.info(f"Successfully uploaded updated Excel file to GCS: gs://{self.bucket_name}/{blob_path}")