import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..core.config import settings

class NotificationService:
    """A service for sending email notifications using SMTP."""

    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.sender_email = settings.sender_email

    def send_summary_email(self, recipient_email: str, subject: str, body_html: str):
        """
        Sends a summary email to a specified recipient via SMTP.
        """
        if not all([self.smtp_host, self.smtp_port, self.smtp_user, self.smtp_password, self.sender_email]):
            print("ERROR: SMTP settings are incomplete. Cannot send email.")
            return

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.sender_email
        message["To"] = recipient_email

        # Attach the HTML body
        message.attach(MIMEText(body_html, "html"))

        try:
            print(f"Connecting to SMTP server at {self.smtp_host}:{self.smtp_port}...")
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()  # Secure the connection
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(
                    self.sender_email, recipient_email, message.as_string()
                )
                print("Email sent successfully!")
        except Exception as e:
            print(f"An unexpected error occurred while sending email: {e}")