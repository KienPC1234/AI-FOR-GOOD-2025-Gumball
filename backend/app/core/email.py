from typing import Any, Dict, Optional

from fastapi import BackgroundTasks
from mailjet_rest import Client
from requests.exceptions import RequestException

from app.core.config import settings


def send_email(
    email_to: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send an email using Mailjet.
    """
    mailjet = Client(
        auth=(settings.MAILJET_API_KEY, settings.MAILJET_SECRET_KEY), version="v3.1"
    )

    if not text_content:
        text_content = html_content.replace("<br>", "\n").replace("<p>", "").replace("</p>", "\n")

    data = {
        "Messages": [
            {
                "From": {
                    "Email": settings.MAILJET_SENDER_EMAIL,
                    "Name": settings.MAILJET_SENDER_NAME,
                },
                "To": [{"Email": email_to}],
                "Subject": subject,
                "TextPart": text_content,
                "HTMLPart": html_content,
            }
        ]
    }

    try:
        response = mailjet.send.create(data=data)
        response.raise_for_status()  # Raise an exception for HTTP errors
    except RequestException as e:
        print(f"Error sending email: {e}")
        return {"error": str(e)}
    return response.json()


def send_registration_email(email_to: str, background_tasks: BackgroundTasks) -> None:
    """
    Schedule an email to be sent in the background.
    """
    background_tasks.add_task(_send_email_task, email_to)

def _send_email_task(email_to: str) -> None:
    """
    Actual email-sending logic.
    """
    subject = f"Welcome to {settings.PROJECT_NAME}!"
    html_content = f"""
    <h1>Welcome to {settings.PROJECT_NAME}!</h1>
    <p>Hi {email_to.split('@')[0]},</p>
    <p>Thank you for registering with us. Your account has been created successfully.</p>
    <p>You can now log in to your account and start using our services.</p>
    <p>Best regards,</p>
    <p>The {settings.PROJECT_NAME} Team</p>
    """

    send_email(
        email_to=email_to,
        subject=subject,
        html_content=html_content
    )