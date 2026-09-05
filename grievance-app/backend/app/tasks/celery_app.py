import os
from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "grievance_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
)

celery_app.conf.beat_schedule = {
    "hourly-escalation-check": {
        "task": "app.tasks.escalation_schedule.run_escalation_sweep",
        "schedule": 3600.0,
    },
}
