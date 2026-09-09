"""Django settings for the portfolio-app backend.

Scaffold only (ADR-028, roadmap item 1) — no apps beyond `config` exist
yet, so INSTALLED_APPS carries only Django's own defaults plus
django-celery-beat.
"""

import os
from pathlib import Path
from urllib.parse import urlparse

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = [h for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h]

# --- Guard 2 (ADR-028): environment mismatch refuses to boot -------------
# If ENVIRONMENT=local and the database host isn't a local one, a laptop
# is about to consume production Celery tasks and run against live
# financial records. Refuse to start rather than let that happen quietly.
if os.environ["ENVIRONMENT"] == "local":
    host = urlparse(os.environ["DATABASE_URL"]).hostname
    if host not in {"localhost", "127.0.0.1", "postgres", "db"}:
        raise ImproperlyConfigured(f"ENVIRONMENT=local but DATABASE_URL points at {host}")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_celery_beat",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Database (ADR-001: PostgreSQL + NUMERIC only, never SQLite) ---------
DATABASES = {
    "default": dj_database_url.parse(os.environ["DATABASE_URL"]),
}

# --- Cache / Celery broker (ADR-007, ADR-028) -----------------------------
# Separate logical Redis DBs so a cache flush never eats the task queue.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ["REDIS_CACHE_URL"],
    },
}

CELERY_BROKER_URL = os.environ["CELERY_BROKER_URL"]
CELERY_RESULT_BACKEND = os.environ["CELERY_BROKER_URL"]
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True

# django-celery-beat: schedule and last-run times live in PostgreSQL, so
# they survive Render redeploys (its filesystem is ephemeral) — ADR-028.
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
