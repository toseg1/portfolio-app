"""Django settings for the portfolio-app backend.

Scaffold only (ADR-028, roadmap item 1) — no apps beyond `config` exist
yet, so INSTALLED_APPS carries only Django's own defaults plus
django-celery-beat.
"""

import os
from email.utils import parseaddr
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

# --- Email sender roles (ADR-029) -----------------------------------------
# Templates name a role, never an address — configuration maps roles to
# addresses, so adding a third one later is a config change, not a hunt
# through templates.
EMAIL_DOMAIN = os.environ["EMAIL_DOMAIN"]
EMAIL_FROM_SYSTEM = os.environ["EMAIL_FROM_SYSTEM"]
EMAIL_FROM_ADVISORY = os.environ["EMAIL_FROM_ADVISORY"]
EMAIL_REPLY_TO = os.environ["EMAIL_REPLY_TO"]
EMAIL_OPERATOR_ALERTS = os.environ["EMAIL_OPERATOR_ALERTS"]

# --- Guard 4 (ADR-029): sender domain mismatch refuses to boot -----------
# A sender address must match a DKIM-authorised domain. Editable at
# runtime, someone sets a Gmail address and every email silently lands in
# spam with no error anywhere — so this scans every EMAIL_FROM_* variable
# rather than naming them, making a third sender role automatically
# covered instead of a guard rewrite waiting to be forgotten.
for _var_name, _var_value in os.environ.items():
    if _var_name.startswith("EMAIL_FROM_"):
        _, _address = parseaddr(_var_value)
        if not _address.endswith(f"@{EMAIL_DOMAIN}"):
            raise ImproperlyConfigured(
                f"{_var_name}={_var_value!r} does not belong to EMAIL_DOMAIN={EMAIL_DOMAIN!r}"
            )
del _var_name, _var_value, _address

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

# --- Email transport (ADR-029) --------------------------------------------
# Local: Mailpit (infra/docker-compose.yml) — a fake SMTP server, nothing
# sent is ever real. Production: a real EU-hosted provider, not chosen yet
# (13 — Open Questions).
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "1025"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "false").lower() == "true"
DEFAULT_FROM_EMAIL = EMAIL_FROM_SYSTEM

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
