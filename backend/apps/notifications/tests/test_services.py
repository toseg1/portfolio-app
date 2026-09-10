from unittest.mock import patch

import pytest

from apps.notifications.constants import EmailCategory, EmailStatus
from apps.notifications.models import EmailLog
from apps.notifications.services import queue_email

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def email_settings(settings):
    settings.EMAIL_FROM_SYSTEM = "Portfolio App <hello@example.invalid>"
    settings.EMAIL_REPLY_TO = "hello@example.invalid"


def test_creates_queued_email_log_and_dispatches_task():
    with patch("apps.notifications.services.send_queued_email") as mock_task:
        log = queue_email(
            recipient_email="user@example.com",
            category=EmailCategory.ACCOUNT_INTEGRITY,
            template_key="auth.password_reset",
            template_version="v1",
            language="en",
            sender_role="SYSTEM",
            subject="Reset your password",
            context={"reset_url": "https://example.invalid/reset/token"},
        )

    assert log.status == EmailStatus.QUEUED
    assert log.from_email == "Portfolio App <hello@example.invalid>"
    assert EmailLog.objects.filter(id=log.id).exists()
    mock_task.delay.assert_called_once_with(
        log.id, {"reset_url": "https://example.invalid/reset/token"}
    )


def test_never_sends_synchronously():
    with patch("apps.notifications.services.send_queued_email") as mock_task:
        queue_email(
            recipient_email="user@example.com",
            category=EmailCategory.ASYNC_COMPLETION,
            template_key="imports.completed",
            template_version="v1",
            language="fr",
            sender_role="SYSTEM",
            subject="Import terminé",
            context={},
        )
    # .delay() queues onto Celery; the task body itself is never called
    # directly from the request/service layer.
    mock_task.assert_not_called()
    mock_task.delay.assert_called_once()
