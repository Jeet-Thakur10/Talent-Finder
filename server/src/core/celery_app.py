from celery import Celery  # type: ignore[import-untyped]

from src.config.settings import settings

celery_app = Celery(
    "scoring_service",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_default_queue="jt_talent_finder_queue",
)

# We autodiscover tasks from tasks.py inside src.core
celery_app.autodiscover_tasks(["src.core"])
