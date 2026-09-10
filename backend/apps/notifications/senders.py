"""Sender-role resolution (ADR-029, 15 — Email & Notifications).

Templates and calling code never reference an address directly, only a
role. Configuration maps roles to addresses, so adding or repointing a
sender is a config change, not a hunt through templates.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings

from .constants import SenderRole


@dataclass(frozen=True)
class SenderIdentity:
    from_email: str
    reply_to: str | None


def resolve_sender(role: str) -> SenderIdentity:
    if role == SenderRole.SYSTEM:
        return SenderIdentity(
            from_email=settings.EMAIL_FROM_SYSTEM, reply_to=settings.EMAIL_REPLY_TO
        )
    if role == SenderRole.ADVISORY:
        return SenderIdentity(
            from_email=settings.EMAIL_FROM_ADVISORY, reply_to=settings.EMAIL_REPLY_TO
        )
    if role == SenderRole.OPERATOR_ALERTS:
        return SenderIdentity(from_email=settings.EMAIL_OPERATOR_ALERTS, reply_to=None)
    raise ValueError(f"Unknown sender role: {role!r}")
