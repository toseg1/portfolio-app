"""Django admin's own login view authenticates via `django.contrib.auth.login()`
directly — it never calls allauth's `record_authentication()`, so allauth's own
"did this session recently reauthenticate?" check (used by
`allauth.mfa.totp.internal.flows.activate_totp` — the reauthentication_required
gate meant for an *already logged-in* session performing a sensitive change)
sees a blank slate and always says no, even seconds after a fresh admin login.

Scoped to "/admin/" specifically: allauth's own headless login already calls
`record_authentication` itself, so a global receiver would double-stamp it.
"""

from __future__ import annotations

from allauth.account.internal.flows.login import record_authentication
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.http import HttpRequest


@receiver(user_logged_in)
def record_admin_login(sender, request: HttpRequest, user, **kwargs) -> None:
    if request.path.startswith("/admin/"):
        record_authentication(request, user, method="password")
