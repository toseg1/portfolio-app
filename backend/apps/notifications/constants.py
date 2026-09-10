"""Fixed enumerations for the email/notification tables (04.8).

These are closed, non-extensible technical domains fixed by the schema
itself (04.8 lists each one as a literal VARCHAR value set) — not
client-extensible dimensions, so ADR-004/ADR-025's reference-table rule
does not apply here the way it does to AssetClass or Currency.
"""

from django.db import models


class SenderRole(models.TextChoices):
    """15 — Email & Notifications: templates name a role, never an address."""

    SYSTEM = "SYSTEM", "System"
    ADVISORY = "ADVISORY", "Advisory"
    OPERATOR_ALERTS = "OPERATOR_ALERTS", "Operator alerts"


class EmailCategory(models.TextChoices):
    """Drives opt-out eligibility (15). Matches NotificationPreference.category."""

    ACCOUNT_INTEGRITY = "account_integrity", "Account integrity"
    CONSENT = "consent", "Consent"
    COMMERCIAL = "commercial", "Commercial"
    ASYNC_COMPLETION = "async_completion", "Async completion"
    DIGEST = "digest", "Digest"
    RISK_ALERT = "risk_alert", "Risk alert"
    OPERATOR_ALERT = "operator_alert", "Operator alert"


# 04.8: "A CHECK ... prevents is_enabled = false on account_integrity and
# consent." These categories are necessary to the service and the consent
# model, never a preference (15).
NON_OPTIONAL_CATEGORIES = (EmailCategory.ACCOUNT_INTEGRITY, EmailCategory.CONSENT)


class EmailStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    SENT = "sent", "Sent"
    DELIVERED = "delivered", "Delivered"
    BOUNCED = "bounced", "Bounced"
    COMPLAINED = "complained", "Complained"
    FAILED = "failed", "Failed"


class BounceType(models.TextChoices):
    """Only a hard bounce suppresses (04.8) — a full mailbox is temporary."""

    HARD = "hard", "Hard"
    SOFT = "soft", "Soft"


class SuppressionReason(models.TextChoices):
    HARD_BOUNCE = "hard_bounce", "Hard bounce"
    COMPLAINT = "complaint", "Complaint"
    MANUAL = "manual", "Manual"
    UNSUBSCRIBE_ALL = "unsubscribe_all", "Unsubscribe all"


class SuppressionSource(models.TextChoices):
    PROVIDER_WEBHOOK = "provider_webhook", "Provider webhook"
    ADMIN = "admin", "Admin"
    USER_ACTION = "user_action", "User action"


class NotificationFrequency(models.TextChoices):
    """weekly / monthly for the digest (v2). Null elsewhere."""

    WEEKLY = "weekly", "Weekly"
    MONTHLY = "monthly", "Monthly"
