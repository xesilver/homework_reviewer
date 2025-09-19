# fastapi-app/app/services/notification.py
import boto3
import os
from botocore.exceptions import ClientError

class NotificationService:
    """A service for sending email notifications using Amazon SES."""

    def __init__(self):
        # The AWS region should be set in your Lambda's environment variables
        self.ses_client = boto3.client("ses", region_name=os.environ.get("AWS_REGION"))
        # The verified email address to send emails from
        self.sender_email = os.environ.get("SENDER_EMAIL")

    def send_summary_email(self, recipient_email: str, subject: str, body_html: str):
        """
        Sends a summary email to a specified recipient.
        
        Args:
            recipient_email: The email address of the recipient.
            subject: The subject of the email.
            body_html: The HTML content of the email body.
        """
        if not self.sender_email:
            print("ERROR: SENDER_EMAIL environment variable is not set. Cannot send email.")
            return

        try:
            response = self.ses_client.send_email(
                Destination={"ToAddresses": [recipient_email]},
                Message={
                    "Body": {
                        "Html": {"Charset": "UTF-8", "Data": body_html}
                    },
                    "Subject": {"Charset": "UTF-8", "Data": subject},
                },
                Source=self.sender_email,
            )
            print(f"Email sent successfully! Message ID: {response['MessageId']}")
        except ClientError as e:
            print(f"ERROR: Failed to send email. {e.response['Error']['Message']}")
        except Exception as e:
            print(f"An unexpected error occurred while sending email: {e}")