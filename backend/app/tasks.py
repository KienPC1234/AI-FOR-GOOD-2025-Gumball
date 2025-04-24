from app.core.email import send_email
from celery_app import celery_app

@celery_app.task
def send_email_task(email_to: str, subject: str, html_content: str) -> None:
    send_email(email_to=email_to, subject=subject, html_content=html_content)