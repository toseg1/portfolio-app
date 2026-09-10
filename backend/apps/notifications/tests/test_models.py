import pytest
from django.db import IntegrityError, transaction

from apps.notifications.constants import EmailCategory, EmailStatus
from apps.notifications.models import EmailLog, NotificationPreference, SuppressionList

pytestmark = pytest.mark.django_db


def make_email_log(**overrides):
    defaults = dict(
        recipient_email="user@example.com",
        category=EmailCategory.ACCOUNT_INTEGRITY,
        template_key="auth.password_reset",
        template_version="v1",
        language="en",
        sender_role="SYSTEM",
        from_email="hello@example.invalid",
        subject="Reset your password",
    )
    defaults.update(overrides)
    return EmailLog.objects.create(**defaults)


class TestEmailLog:
    def test_recipient_email_lookup_is_case_insensitive(self):
        make_email_log(recipient_email="User@Example.com")
        assert EmailLog.objects.filter(recipient_email="user@example.com").exists()

    def test_mark_sent_updates_status_and_timestamp(self):
        log = make_email_log()
        assert log.status == EmailStatus.QUEUED
        log.mark_sent(provider="smtp", provider_message_id="abc123")
        log.refresh_from_db()
        assert log.status == EmailStatus.SENT
        assert log.provider == "smtp"
        assert log.provider_message_id == "abc123"
        assert log.sent_at is not None

    def test_mark_failed_records_error(self):
        log = make_email_log()
        log.mark_failed(error="boom")
        log.refresh_from_db()
        assert log.status == EmailStatus.FAILED
        assert log.error == "boom"


class TestSuppressionList:
    def test_email_unique_case_insensitive(self):
        SuppressionList.objects.create(
            email="bounced@example.com", reason="hard_bounce", source="provider_webhook"
        )
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                SuppressionList.objects.create(
                    email="Bounced@Example.com", reason="hard_bounce", source="provider_webhook"
                )

    def test_release_leaves_row_in_place(self):
        from django.utils import timezone

        entry = SuppressionList.objects.create(
            email="fixed@example.com", reason="manual", source="admin"
        )
        entry.released_at = timezone.now()
        entry.save(update_fields=["released_at"])
        assert SuppressionList.objects.filter(id=entry.id).exists()


class TestNotificationPreference:
    def test_transactional_category_cannot_be_disabled(self):
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                NotificationPreference.objects.create(
                    user_id=1, category=EmailCategory.ACCOUNT_INTEGRITY, is_enabled=False
                )

    def test_consent_category_cannot_be_disabled(self):
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                NotificationPreference.objects.create(
                    user_id=1, category=EmailCategory.CONSENT, is_enabled=False
                )

    def test_optional_category_can_be_disabled(self):
        pref = NotificationPreference.objects.create(
            user_id=1, category=EmailCategory.ASYNC_COMPLETION, is_enabled=False
        )
        assert pref.pk is not None

    def test_unique_per_user_and_category(self):
        NotificationPreference.objects.create(user_id=1, category=EmailCategory.DIGEST)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                NotificationPreference.objects.create(user_id=1, category=EmailCategory.DIGEST)
