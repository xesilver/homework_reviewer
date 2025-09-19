"""
Excel handling service for storing and retrieving review results.
"""
import pandas as pd
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from openpyxl.styles import Font, PatternFill, Alignment

from ..core import logger, ensure_directory
from ..core.config import settings
from ..models.schemas import ReviewResponse


class ExcelService:
    """Service for handling Excel files with review results."""

    def __init__(self, results_dir: Optional[Path] = None):
        self.results_dir = results_dir or settings.results_dir
        ensure_directory(self.results_dir)

    def get_excel_file_path(self, lecture_number: int) -> Path:
        """
        Get the Excel file path for a specific lecture.
        """
        return self.results_dir / f"lecture_{lecture_number}_reviews.xlsx"

    def create_excel_template(self, lecture_number: int, usernames: List[str], tasks: List[str]) -> Path:
        """
        Create an Excel template for storing review results.
        """
        excel_path = self.get_excel_file_path(lecture_number)

        data = []
        for username in usernames:
            for task in tasks:
                data.append({
                    'Username': username,
                    'Lecture': lecture_number,
                    'Task': task,
                    'Score (%)': 0,
                    'Comments': '',
                    'Technical Correctness': 0,
                    'Code Style': 0,
                    'Documentation': 0,
                    'Performance': 0,
                    'Review Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

        df = pd.DataFrame(data)

        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Reviews', index=False)
            worksheet = writer.sheets['Reviews']
            self._format_excel_sheet(worksheet, df)

        logger.info(f"Created Excel template: {excel_path}")
        return excel_path

    def _format_excel_sheet(self, worksheet, df: pd.DataFrame) -> None:
        """
        Apply formatting to the Excel worksheet.
        """
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")

        for cell in worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

        worksheet.freeze_panes = 'A2'

    def update_student_review(self, lecture_number: int, review_response: ReviewResponse) -> None:
        """
        Update Excel file with review results for a student.
        """
        excel_path = self.get_excel_file_path(lecture_number)

        if excel_path.exists():
            df = pd.read_excel(excel_path, sheet_name='Reviews')
        else:
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

        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Reviews', index=False)
            worksheet = writer.sheets['Reviews']
            self._format_excel_sheet(worksheet, df)

        logger.info(f"Updated Excel file for lecture {lecture_number}: {excel_path}")

    def get_student_reviews(self, lecture_number: int, username: Optional[str] = None) -> pd.DataFrame:
        """
        Get review results from Excel file.
        """
        excel_path = self.get_excel_file_path(lecture_number)

        if not excel_path.exists():
            logger.warning(f"Excel file not found: {excel_path}")
            return pd.DataFrame()

        df = pd.read_excel(excel_path, sheet_name='Reviews')

        if username:
            df = df[df['Username'] == username]

        return df