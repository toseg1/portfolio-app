"""EmailLog, SuppressionList, NotificationPreference (04.8).

FK note: `accounts.User` now exists (roadmap item 1) — every `user_id` below
(`EmailLog`, `NotificationPreference`) is a real ForeignKey. `EmailLog.client_id`
stays a plain column: `accounts.Client` doesn't exist yet. Add that real
ForeignKey and a migration once it does — do not let it be forgotten.
"""

from django.db import models

from .constants import (
    NON_OPTIONAL_CATEGORIES,
    BounceType,
    EmailCategory,
    EmailStatus,
    NotificationFrequency,
    SenderRole,
    SuppressionReason,
    SuppressionSource,
)
from .fields import CITextField


class EmailLog(models.Model):
    """What was sent, to whom, and what happened to it. Append-only.

    Never store the rendered body (08, 04.8) — template_key +
    template_version + language + the related object is enough to
    reconstruct what was sent. The only legitimate mutations after
    creation are the status-transition helpers below (mark_sent,
    mark_failed) and, later, the delivery webhook handler.
    """

    recipient_email = CITextField()
    user = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="email_logs"
    )
    client_id = models.UUIDField(null=True, blank=True)

    category = models.CharField(max_length=40, choices=EmailCategory.choices)
    template_key = models.CharField(max_length=60)
    template_version = models.CharField(max_length=20)
    language = models.CharField(max_length=5)

    sender_role = models.CharField(max_length=20, choices=SenderRole.choices)
    from_email = models.CharField(max_length=160)
    subject = models.CharField(max_length=255)

    provider = models.CharField(max_length=30, blank=True, default="")
    provider_message_id = models.CharField(max_length=120, null=True, blank=True)

    status = models.CharField(
        max_length=20, choices=EmailStatus.choices, default=EmailStatus.QUEUED
    )
    bounce_type = models.CharField(max_length=20, choices=BounceType.choices, null=True, blank=True)
    error = models.TextField(null=True, blank=True)

    related_object_type = models.CharField(max_length=40, null=True, blank=True)
    related_object_id = models.CharField(max_length=60, null=True, blank=True)

    queued_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    bounced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "email_log"
        indexes = [
            models.Index(fields=["recipient_email", "-queued_at"], name="email_log_recipient_idx"),
            models.Index(fields=["user", "-queued_at"], name="email_log_user_idx"),
            models.Index(fields=["category", "-queued_at"], name="email_log_category_idx"),
            models.Index(
                fields=["status"],
                name="email_log_open_status_idx",
                condition=models.Q(status__in=[EmailStatus.QUEUED, EmailStatus.FAILED]),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.template_key} -> {self.recipient_email} ({self.status})"

    def mark_sent(self, *, provider: str, provider_message_id: str | None = None) -> None:
        from django.utils import timezone

        self.status = EmailStatus.SENT
        self.provider = provider
        self.provider_message_id = provider_message_id
        self.sent_at = timezone.now()
        self.save(update_fields=["status", "provider", "provider_message_id", "sent_at"])

    def mark_failed(self, *, error: str) -> None:
        self.status = EmailStatus.FAILED
        self.error = error
        self.save(update_fields=["status", "error"])


class SuppressionList(models.Model):
    """Addresses that must never be emailed again. Checked before every send.

    Global, not client-scoped — it protects the sending domain's
    reputation, which is shared by everyone.
    """

    email = CITextField(unique=True)
    reason = models.CharField(max_length=20, choices=SuppressionReason.choices)
    source = models.CharField(max_length=20, choices=SuppressionSource.choices)
    email_log = models.ForeignKey(
        EmailLog, null=True, blank=True, on_delete=models.SET_NULL, related_name="suppressions"
    )
    note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "suppression_list"

    def __str__(self) -> str:
        return self.email


class NotificationPreference(models.Model):
    """Per user, per category. Transactional categories cannot be disabled."""

    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="notification_preferences"
    )
    category = models.CharField(max_length=40, choices=EmailCategory.choices)
    is_enabled = models.BooleanField(default=True)
    frequency = models.CharField(
        max_length=20, choices=NotificationFrequency.choices, null=True, blank=True
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notification_preference"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "category"], name="uniq_notification_preference_user_category"
            ),
            models.CheckConstraint(
                condition=~models.Q(category__in=list(NON_OPTIONAL_CATEGORIES))
                | models.Q(is_enabled=True),
                name="notification_preference_transactional_always_enabled",
            ),
        ]

    def __str__(self) -> str:
        return f"user={self.user_id} {self.category}={self.is_enabled}"
