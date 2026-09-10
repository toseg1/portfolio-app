"""The actual send path (15 — Email & Notifications, ADR-009's Celery-only rule).

The suppression list is checked here, at the point of actual sending —
not when the caller queues the email — because an unrelated bounce can
suppress the address in the gap between those two moments.
"""

from __future__ import annotations

import logging
from smtplib import SMTPException
from typing import Any

from celery import Task, shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .constants import SenderRole
from .models import EmailLog, SuppressionList
from .senders import resolve_sender

logger = logging.getLogger(__name__)

_MAX_RETRIES = 5


def _footer_context() -> dict[str, Any]:
    return {
        "legal_entity_name": settings.LEGAL_ENTITY_NAME,
        "legal_entity_address": settings.LEGAL_ENTITY_ADDRESS,
        "cif_registration_number": settings.CIF_REGISTRATION_NUMBER,
        "orias_number": settings.ORIAS_NUMBER,
    }


def _alert_operator(log: EmailLog, exc: BaseException) -> None:
    if log.sender_role == SenderRole.OPERATOR_ALERTS:
        # Don't alert about a failure to alert — that loops forever.
        logger.error("Operator alert email (EmailLog #%s) itself failed to send: %s", log.id, exc)
        return
    try:
        sender = resolve_sender(SenderRole.OPERATOR_ALERTS)
        EmailMultiAlternatives(
            subject=f"Email delivery failed: {log.template_key}",
            body=(
                f"EmailLog #{log.id} to {log.recipient_email} "
                f"(template {log.template_key}, category {log.category}) "
                f"failed after retries: {exc}"
            ),
            from_email=sender.from_email,
            to=[sender.from_email],
        ).send()
    except Exception:
        logger.exception("Failed to send operator alert for EmailLog #%s", log.id)


def handle_final_failure(email_log_id: int, exc: BaseException) -> None:
    """Called once retries are exhausted (or on a non-retryable error)."""
    try:
        log = EmailLog.objects.get(id=email_log_id)
    except EmailLog.DoesNotExist:
        logger.error("handle_final_failure: EmailLog #%s no longer exists", email_log_id)
        return
    log.mark_failed(error=str(exc))
    _alert_operator(log, exc)


class _EmailSendTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        email_log_id = args[0] if args else kwargs.get("email_log_id")
        if email_log_id is not None:
            handle_final_failure(email_log_id, exc)


@shared_task(
    bind=True,
    base=_EmailSendTask,
    autoretry_for=(SMTPException, ConnectionError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=_MAX_RETRIES,
)
def send_queued_email(self, email_log_id: int, context: dict[str, Any]) -> None:
    try:
        log = EmailLog.objects.get(id=email_log_id)
    except EmailLog.DoesNotExist:
        logger.error("send_queued_email: EmailLog #%s no longer exists", email_log_id)
        return

    if SuppressionList.objects.filter(email=log.recipient_email, released_at__isnull=True).exists():
        log.mark_failed(error="recipient is suppressed")
        return

    sender = resolve_sender(log.sender_role)
    render_context = {**_footer_context(), **context, "language": log.language}

    html_body = render_to_string(
        f"notifications/emails/{log.template_key}/{log.language}/body.html", render_context
    )
    text_body = render_to_string(
        f"notifications/emails/{log.template_key}/{log.language}/body.txt", render_context
    )

    message = EmailMultiAlternatives(
        subject=log.subject,
        body=text_body,
        from_email=log.from_email,
        to=[log.recipient_email],
        reply_to=[sender.reply_to] if sender.reply_to else None,
    )
    message.attach_alternative(html_body, "text/html")
    message.send()

    log.mark_sent(provider="smtp")
