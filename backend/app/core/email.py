from typing import Any, Dict, Optional

from mailjet_rest import Client

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

    response = mailjet.send.create(data=data)
    return response.json()


def send_registration_email(email_to: str) -> Dict[str, Any]:
    """
    Send a registration confirmation email.
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

    return send_email(
        email_to=email_to,
        subject=subject,
        html_content=html_content,
    )
