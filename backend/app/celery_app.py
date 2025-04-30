from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "AFG_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)
celery_app.conf.task_routes = {"app.tasks.*": {"queue": "ai_queue"}}