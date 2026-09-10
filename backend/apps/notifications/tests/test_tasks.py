from unittest.mock import patch

import pytest
from django.core import mail
from django.utils import timezone

from apps.notifications.constants import EmailCategory, EmailStatus, SenderRole
from apps.notifications.models import EmailLog, SuppressionList
from apps.notifications.tasks import handle_final_failure, send_queued_email

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def email_settings(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.EMAIL_FROM_SYSTEM = "Portfolio App <hello@example.invalid>"
    settings.EMAIL_REPLY_TO = "hello@example.invalid"
    settings.EMAIL_OPERATOR_ALERTS = "ops@example.invalid"
    settings.LEGAL_ENTITY_NAME = ""
    settings.LEGAL_ENTITY_ADDRESS = ""
    settings.CIF_REGISTRATION_NUMBER = ""
    settings.ORIAS_NUMBER = ""


def make_email_log(**overrides):
    defaults = dict(
        recipient_email="user@example.com",
        category=EmailCategory.ACCOUNT_INTEGRITY,
        template_key="auth.password_reset",
        template_version="v1",
        language="en",
        sender_role=SenderRole.SYSTEM,
        from_email="Portfolio App <hello@example.invalid>",
        subject="Reset your password",
    )
    defaults.update(overrides)
    return EmailLog.objects.create(**defaults)


class TestSendQueuedEmail:
    def test_suppressed_recipient_is_never_sent(self):
        SuppressionList.objects.create(
            email="user@example.com", reason="hard_bounce", source="provider_webhook"
        )
        log = make_email_log()

        send_queued_email(log.id, {})

        log.refresh_from_db()
        assert log.status == EmailStatus.FAILED
        assert log.error == "recipient is suppressed"
        assert len(mail.outbox) == 0

    def test_released_suppression_does_not_block_sending(self):
        SuppressionList.objects.create(
            email="user@example.com", reason="manual", source="admin", released_at=timezone.now()
        )
        log = make_email_log()

        with patch("apps.notifications.tasks.render_to_string", return_value="rendered"):
            send_queued_email(log.id, {})

        log.refresh_from_db()
        assert log.status == EmailStatus.SENT
        assert len(mail.outbox) == 1

    def test_successful_send_marks_log_sent(self):
        log = make_email_log()

        with patch("apps.notifications.tasks.render_to_string", return_value="rendered body"):
            send_queued_email(log.id, {"reset_url": "https://example.invalid/x"})

        log.refresh_from_db()
        assert log.status == EmailStatus.SENT
        assert log.provider == "smtp"
        assert log.sent_at is not None

        sent = mail.outbox[0]
        assert sent.to == ["user@example.com"]
        assert sent.from_email == "Portfolio App <hello@example.invalid>"
        assert sent.subject == "Reset your password"
        assert sent.alternatives[0][1] == "text/html"

    def test_missing_email_log_does_not_raise(self):
        send_queued_email(999999, {})  # no EmailLog with this id


class TestHandleFinalFailure:
    def test_marks_log_failed_and_alerts_operator(self):
        log = make_email_log()

        handle_final_failure(log.id, RuntimeError("smtp exploded"))

        log.refresh_from_db()
        assert log.status == EmailStatus.FAILED
        assert "smtp exploded" in log.error
        assert len(mail.outbox) == 1
        alert = mail.outbox[0]
        assert alert.to == ["ops@example.invalid"]
        assert "auth.password_reset" in alert.body

    def test_operator_alert_failure_does_not_recurse(self):
        log = make_email_log(
            sender_role=SenderRole.OPERATOR_ALERTS, category=EmailCategory.OPERATOR_ALERT
        )

        handle_final_failure(log.id, RuntimeError("smtp exploded"))

        log.refresh_from_db()
        assert log.status == EmailStatus.FAILED
        # No second alert email attempted for a failed operator alert itself.
        assert len(mail.outbox) == 0

    def test_missing_email_log_does_not_raise(self):
        handle_final_failure(999999, RuntimeError("whatever"))
