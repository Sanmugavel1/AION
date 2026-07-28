"""
AION Celery Application — Background Task Processing
"""
from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "aion",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.sensing_worker",
        "app.workers.decay_worker",
        "app.workers.disease_worker",
        "app.workers.intelligence_worker",
        "app.workers.report_worker",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "aion.sensing.*": {"queue": "sensing"},
        "aion.decay.*": {"queue": "analysis"},
        "aion.disease.*": {"queue": "analysis"},
        "aion.intelligence.*": {"queue": "intelligence"},
        "aion.advisor.*": {"queue": "reports"},
    },
    beat_schedule={
        # Module 1: Sensing — every 5 minutes
        "aion-sensing-all-sources": {
            "task": "aion.sensing.ingest_all_sources",
            "schedule": crontab(minute="*/5"),
            "args": [],
        },
        # Module 4: Decay — every hour
        "aion-decay-scan": {
            "task": "aion.decay.scan",
            "schedule": crontab(minute=0),
            "args": [],
        },
        # Module 5: Disease detection — every 6 hours
        "aion-disease-detect": {
            "task": "aion.disease.detect",
            "schedule": crontab(minute=0, hour="*/6"),
            "args": [],
        },
        # Module 9: Intelligence Index — daily at midnight
        "aion-intelligence-compute": {
            "task": "aion.intelligence.compute",
            "schedule": crontab(minute=0, hour=0),
            "args": [],
        },
        # Module 10: Board report — every Monday at 8am UTC
        "aion-board-report": {
            "task": "aion.advisor.weekly_report",
            "schedule": crontab(minute=0, hour=8, day_of_week="monday"),
            "args": [],
        },
    },
)
