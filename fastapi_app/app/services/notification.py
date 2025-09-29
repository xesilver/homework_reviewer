import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from ..core.config import settings

class NotificationService:
    """A service for sending email notifications using SendGrid."""

    def __init__(self):
        self.sendgrid_client = SendGridAPIClient(settings.sendgrid_api_key)
        self.sender_email = settings.sender_email

    def send_summary_email(self, recipient_email: str, subject: str, body_html: str):
        """
        Sends a summary email to a specified recipient.
        """
        if not self.sender_email or not self.sendgrid_client.api_key:
            print("ERROR: SENDER_EMAIL or SendGrid API key is not set. Cannot send email.")
            return

        message = Mail(
            from_email=self.sender_email,
            to_emails=recipient_email,
            subject=subject,
            html_content=body_html
        )
        try:
            response = self.sendgrid_client.send(message)
            print(f"Email sent successfully! Status Code: {response.status_code}")
        except Exception as e:
            print(f"An unexpected error occurred while sending email: {e}")