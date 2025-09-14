"""
Excel handling service for storing and retrieving review results.
"""
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows

from ..core import logger, ensure_directory
from ..core.config import settings
from ..models.schemas import ReviewResponse, TaskReview


class ExcelService:
    """Service for handling Excel files with review results."""
    
    def __init__(self, results_dir: Optional[Path] = None):
        self.results_dir = results_dir or settings.results_dir
        ensure_directory(self.results_dir)
    
    def get_excel_file_path(self, lecture_number: int) -> Path:
        """
        Get the Excel file path for a specific lecture.
        
        Args:
            lecture_number: Lecture number
            
        Returns:
            Path to the Excel file
        """
        return self.results_dir / f"lecture_{lecture_number}_reviews.xlsx"
    
    def create_excel_template(self, lecture_number: int, students: List[str], tasks: List[str]) -> Path:
        """
        Create an Excel template for storing review results.
        
        Args:
            lecture_number: Lecture number
            students: List of student surnames
            tasks: List of task identifiers
            
        Returns:
            Path to the created Excel file
        """
        excel_path = self.get_excel_file_path(lecture_number)
        
        # Create DataFrame with students and tasks
        data = []
        for student in students:
            for task in tasks:
                data.append({
                    'Surname': student,
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
        
        # Save to Excel with formatting
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Reviews', index=False)
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Reviews']
            
            # Apply formatting
            self._format_excel_sheet(worksheet, df)
        
        logger.info(f"Created Excel template: {excel_path}")
        return excel_path
    
    def _format_excel_sheet(self, worksheet, df: pd.DataFrame) -> None:
        """
        Apply formatting to the Excel worksheet.
        
        Args:
            worksheet: OpenPyXL worksheet object
            df: DataFrame with the data
        """
        # Header formatting
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        
        for cell in worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Auto-adjust column widths
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
        
        # Freeze the header row
        worksheet.freeze_panes = 'A2'
    
    def update_student_review(self, lecture_number: int, review_response: ReviewResponse) -> None:
        """
        Update Excel file with review results for a student.
        
        Args:
            lecture_number: Lecture number
            review_response: Review response with results
        """
        excel_path = self.get_excel_file_path(lecture_number)
        
        # Load existing data or create new
        if excel_path.exists():
            df = pd.read_excel(excel_path, sheet_name='Reviews')
        else:
            # Create new DataFrame if file doesn't exist
            df = pd.DataFrame(columns=[
                'Surname', 'Lecture', 'Task', 'Score (%)', 'Comments',
                'Technical Correctness', 'Code Style', 'Documentation', 
                'Performance', 'Review Date'
            ])
        
        # Update or add rows for each task
        for task_review in review_response.details:
            # Check if row exists - convert both to string for comparison to handle type mismatches
            mask = (df['Surname'] == review_response.surname) & (df['Task'].astype(str) == str(task_review.task))
            
            if mask.any():
                # Update existing row
                df.loc[mask, 'Score (%)'] = task_review.score
                df.loc[mask, 'Comments'] = task_review.comments
                df.loc[mask, 'Technical Correctness'] = task_review.technical_correctness
                df.loc[mask, 'Code Style'] = task_review.code_style
                df.loc[mask, 'Documentation'] = task_review.documentation
                df.loc[mask, 'Performance'] = task_review.performance
                df.loc[mask, 'Review Date'] = task_review.review_timestamp.strftime('%Y-%m-%d %H:%M:%S')
            else:
                # Add new row
                new_row = {
                    'Surname': review_response.surname,
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
        
        # Save updated data
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Reviews', index=False)
            
            # Apply formatting
            workbook = writer.book
            worksheet = writer.sheets['Reviews']
            self._format_excel_sheet(worksheet, df)
        
        logger.info(f"Updated Excel file for lecture {lecture_number}: {excel_path}")
    
    def remove_duplicate_entries(self, lecture_number: int) -> None:
        """
        Remove duplicate entries from Excel file, keeping the most recent review for each student-task combination.
        
        Args:
            lecture_number: Lecture number
        """
        excel_path = self.get_excel_file_path(lecture_number)
        
        if not excel_path.exists():
            logger.warning(f"Excel file not found: {excel_path}")
            return
        
        df = pd.read_excel(excel_path, sheet_name='Reviews')
        
        if df.empty:
            return
        
        logger.info(f"Before cleanup: {len(df)} entries")
        
        # Convert Review Date to datetime for proper sorting
        df['Review Date'] = pd.to_datetime(df['Review Date'])
        
        # Convert Task column to string to handle mixed data types
        df['Task'] = df['Task'].astype(str)
        
        # Sort by Review Date descending to keep most recent entries
        df = df.sort_values(['Surname', 'Task', 'Review Date'], ascending=[True, True, False])
        
        # Remove duplicates, keeping the first (most recent) entry for each student-task combination
        df_cleaned = df.drop_duplicates(subset=['Surname', 'Task'], keep='first')
        
        logger.info(f"After cleanup: {len(df_cleaned)} entries")
        
        # Sort back to original order
        df_cleaned = df_cleaned.sort_values(['Surname', 'Task'])
        
        # Save cleaned data
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df_cleaned.to_excel(writer, sheet_name='Reviews', index=False)
            
            # Apply formatting
            workbook = writer.book
            worksheet = writer.sheets['Reviews']
            self._format_excel_sheet(worksheet, df_cleaned)
        
        logger.info(f"Removed duplicate entries from Excel file for lecture {lecture_number}")
    
    def get_student_reviews(self, lecture_number: int, surname: Optional[str] = None) -> pd.DataFrame:
        """
        Get review results from Excel file.
        
        Args:
            lecture_number: Lecture number
            surname: Optional student surname to filter by
            
        Returns:
            DataFrame with review results
        """
        excel_path = self.get_excel_file_path(lecture_number)
        
        if not excel_path.exists():
            logger.warning(f"Excel file not found: {excel_path}")
            return pd.DataFrame()
        
        df = pd.read_excel(excel_path, sheet_name='Reviews')
        
        if surname:
            df = df[df['Surname'] == surname]
        
        return df
    
    def get_lecture_summary(self, lecture_number: int) -> Dict[str, Any]:
        """
        Get summary statistics for a lecture.
        
        Args:
            lecture_number: Lecture number
            
        Returns:
            Dictionary with summary statistics
        """
        df = self.get_student_reviews(lecture_number)
        
        if df.empty:
            return {
                "total_students": 0,
                "total_tasks": 0,
                "average_score": 0,
                "completion_rate": 0
            }
        
        summary = {
            "total_students": int(df['Surname'].nunique()),
            "total_tasks": int(df['Task'].nunique()),
            "average_score": int(df['Score (%)'].mean()),
            "completion_rate": int((df['Score (%)'] > 0).mean() * 100),
            "score_distribution": {
                "excellent": int((df['Score (%)'] >= 90).sum()),
                "good": int(((df['Score (%)'] >= 80) & (df['Score (%)'] < 90)).sum()),
                "satisfactory": int(((df['Score (%)'] >= 70) & (df['Score (%)'] < 80)).sum()),
                "needs_improvement": int((df['Score (%)'] < 70).sum())
            }
        }
        
        return summary
    
    def export_to_csv(self, lecture_number: int, output_path: Optional[Path] = None) -> Path:
        """
        Export review results to CSV format.
        
        Args:
            lecture_number: Lecture number
            output_path: Optional custom output path
            
        Returns:
            Path to the exported CSV file
        """
        df = self.get_student_reviews(lecture_number)
        
        if output_path is None:
            output_path = self.results_dir / f"lecture_{lecture_number}_reviews.csv"
        
        df.to_csv(output_path, index=False)
        logger.info(f"Exported CSV file: {output_path}")
        
        return output_path
