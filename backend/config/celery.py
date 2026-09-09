"""Celery application for the portfolio-app backend.

Beat runs embedded in this single worker process
(`celery -A config worker --beat`), never as its own service — ADR-028,
to stay inside the Render EUR30/month ceiling. If a second worker is ever
added, Beat must move to its own service.
"""

import os
import sys
from datetime import date

from celery import Celery
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# --- Guard 1 (ADR-028): Beat runs only where explicitly enabled ----------
# ENABLE_BEAT=true is set on the Render worker service (and, locally, only
# on the `worker` service in infra/docker-compose.yml) and nowhere else.
if "--beat" in sys.argv and os.environ.get("ENABLE_BEAT") != "true":
    raise ImproperlyConfigured("Beat is not enabled in this environment")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


def run_once_per_day(task_name: str, as_of: date) -> bool:
    """Guard 3 (ADR-028): date-keyed lock for every Beat-scheduled task.

    Makes a double-fire harmless regardless of cause (redeploy overlap, a
    second worker added without moving Beat, a laptop pointed at
    production). Call at the top of every scheduled task and return early
    if this comes back False.
    """
    return cache.add(f"beat:{task_name}:{as_of.isoformat()}", "1", timeout=36 * 3600)
