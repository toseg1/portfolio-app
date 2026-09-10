"""Routes every allauth email through the notifications queue (backend/CLAUDE.md:
"callers never touch SMTP or the suppression list directly — call queue_email(...)").

allauth's own Django-template email rendering is bypassed entirely — `send_mail`
is the one low-level method every higher-level allauth email helper
(`send_confirmation_mail`, `send_password_reset_mail`, `send_account_already_exists_mail`)
funnels through, so intercepting it here is enough to cover every flow this app's
settings can actually trigger (no social accounts, no phone verification, no
login-by-code). An unmapped `template_prefix` fails loudly rather than silently
falling back to allauth's default SMTP path, which would bypass the suppression
list and `EmailLog` audit trail — consistent with this repo's other guards.
"""

from __future__ import annotations

from typing import Any

from allauth.account.adapter import DefaultAccountAdapter
from django.utils.translation import get_language

from apps.notifications.constants import EmailCategory, SenderRole
from apps.notifications.services import queue_email

_TEMPLATE_KEYS = {
    "account/email/email_confirmation_signup": "auth.email_confirmation",
    "account/email/email_confirmation": "auth.email_confirmation",
    "account/email/password_reset_key": "auth.password_reset",
    "account/email/account_already_exists": "auth.account_already_exists",
    "account/email/unknown_account": "auth.unknown_account",
}

_SUBJECTS = {
    "auth.email_confirmation": {
        "en": "Confirm your email address",
        "fr": "Confirmez votre adresse e-mail",
    },
    "auth.password_reset": {
        "en": "Reset your password",
        "fr": "Réinitialisez votre mot de passe",
    },
    "auth.account_already_exists": {
        "en": "Someone tried to sign up with your email",
        "fr": "Quelqu'un a tenté de s'inscrire avec votre e-mail",
    },
    "auth.unknown_account": {
        "en": "You don't have an account yet",
        "fr": "Vous n'avez pas encore de compte",
    },
}

_URL_CONTEXT_KEYS = ("activate_url", "password_reset_url", "signup_url")


class AccountAdapter(DefaultAccountAdapter):
    def send_mail(self, template_prefix: str, email: str, context: dict[str, Any]) -> None:
        template_key = _TEMPLATE_KEYS.get(template_prefix)
        if template_key is None:
            raise NotImplementedError(
                f"No notifications template mapped for allauth email {template_prefix!r} — "
                "map it in apps.accounts.adapters._TEMPLATE_KEYS rather than let it bypass "
                "the notifications queue."
            )

        language = (get_language() or "en")[:2]
        subjects = _SUBJECTS[template_key]
        if language not in subjects:
            language = "en"

        url = next((context[k] for k in _URL_CONTEXT_KEYS if context.get(k)), None)
        queue_email(
            recipient_email=email,
            category=EmailCategory.ACCOUNT_INTEGRITY,
            template_key=template_key,
            template_version="v1",
            language=language,
            sender_role=SenderRole.SYSTEM,
            subject=subjects[language],
            context={"url": url},
        )
