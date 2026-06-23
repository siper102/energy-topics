import os
from celery import Celery

# Get Redis URL from environment variables
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize Celery
celery_app = Celery("optimization_worker", broker=REDIS_URL, backend=REDIS_URL)

# Optional configuration
celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

# Auto-discover tasks from tasks.py
celery_app.autodiscover_tasks(["tasks"])
