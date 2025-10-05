import pandas as pd
from pathlib import Path
import io
import os
from datetime import timedelta
from typing import Optional

from google.cloud import storage
import google.auth
from google.auth import impersonated_credentials

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

        try:
            bucket = self.gcs_client.bucket(self.bucket_name)
            blob_path = self.get_excel_blob_path(lecture_number)
            blob = bucket.blob(blob_path)

            if not blob.exists():
                logger.warning(f"Excel file not found in GCS: gs://{self.bucket_name}/{blob_path}")
                return pd.DataFrame()

            file_content = blob.download_as_bytes()
            df = pd.read_excel(io.BytesIO(file_content), sheet_name='Reviews')
            
            if username:
                df = df[df['Username'] == username]

            return df
        except Exception as e:
            logger.error(f"Failed to get student reviews from GCS: {e}")
            return pd.DataFrame()

    def get_excel_signed_url(self, lecture_number: int) -> Optional[str]:
        """Generates a signed URL to download the Excel file using the IAM API."""
        if not self.bucket_name or not settings.service_account_email:
            logger.error("GCS_BUCKET_NAME or SERVICE_ACCOUNT_EMAIL environment variable not set.")
            return None
        
        try:
            # Get the application's default credentials
            source_credentials, project = google.auth.default()
            
            # Create impersonated credentials, which can act as a signer.
            signing_credentials = impersonated_credentials.Credentials(
                source_credentials=source_credentials,
                target_principal=settings.service_account_email,
                target_scopes=["https://www.googleapis.com/auth/devstorage.read_only"],
            )

            bucket = self.gcs_client.bucket(self.bucket_name)
            blob_path = self.get_excel_blob_path(lecture_number)
            blob = bucket.blob(blob_path)

            if not blob.exists():
                logger.warning(f"Cannot generate signed URL. File not found: gs://{self.bucket_name}/{blob_path}")
                return None

            # The blob object's generate_signed_url method can directly use the
            # impersonated credentials to sign the URL.
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=1),
                method="GET",
                credentials=signing_credentials,
            )
            
            logger.info("Successfully generated signed URL using IAM.")
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate signed URL with IAM: {e}")
            return None

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
            file_content = blob.download_as_bytes()
            df = pd.read_excel(io.BytesIO(file_content), sheet_name='Reviews')
            logger.info(f"Loaded existing Excel file from GCS: gs://{self.bucket_name}/{blob_path}")
        except Exception:
            logger.info("Excel file not found in GCS. Creating a new one.")
            df = pd.DataFrame(columns=[
                'Username', 'Lecture', 'Task', 'Score (%)', 'Comments',
                'Technical Correctness', 'Code Style', 'Documentation',
                'Performance', 'Review Date'
            ])
            
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

        output_buffer = io.BytesIO()
        with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Reviews', index=False)

        output_buffer.seek(0)
        blob.upload_from_file(output_buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        logger.info(f"Successfully uploaded updated Excel file to GCS: gs://{self.bucket_name}/{blob_path}")