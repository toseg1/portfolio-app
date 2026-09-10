"""Queueing entry point for transactional email (15 — Email & Notifications).

Callers describe *what* to send; this records the attempt and hands the
actual render-and-send to the Celery worker (ADR-009's Celery-only rule —
never the request cycle). `context` must be JSON-serialisable: it is sent
to the worker as Celery task arguments, not stored on `EmailLog`.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from .constants import EmailStatus
from .models import EmailLog
from .senders import resolve_sender
from .tasks import send_queued_email


def queue_email(
    *,
    recipient_email: str,
    category: str,
    template_key: str,
    template_version: str,
    language: str,
    sender_role: str,
    subject: str,
    context: dict[str, Any],
    user_id: int | None = None,
    client_id: UUID | None = None,
    related_object_type: str | None = None,
    related_object_id: str | None = None,
) -> EmailLog:
    sender = resolve_sender(sender_role)

    log = EmailLog.objects.create(
        recipient_email=recipient_email,
        user_id=user_id,
        client_id=client_id,
        category=category,
        template_key=template_key,
        template_version=template_version,
        language=language,
        sender_role=sender_role,
        from_email=sender.from_email,
        subject=subject,
        status=EmailStatus.QUEUED,
        related_object_type=related_object_type,
        related_object_id=related_object_id,
    )

    send_queued_email.delay(log.id, context)
    return log
