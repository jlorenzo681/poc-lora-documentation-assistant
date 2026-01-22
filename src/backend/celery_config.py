import os
from celery import Celery

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery(
    "rag_backend",
    broker=broker_url,
    backend=result_backend,
    include=["src.backend.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Beat Schedule
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'sync-all-connectors-every-15-mins': {
        'task': 'src.backend.tasks.sync_all_connectors_task',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
}
