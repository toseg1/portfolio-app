"""Gates Django admin behind staff + TOTP MFA (Notion "08 — Security, Privacy &
GDPR": admin must be staff-only, MFA-required, rate-limited). "Staff-only" and
"rate-limited" already fall out of Django's own admin (`is_staff` gate) and
axes (which hooks the authentication backend chain admin login also goes
through) respectively — this middleware is the one genuinely new piece:
forcing TOTP enrolment/verification before a staff session can reach `/admin/`.
"""

from __future__ import annotations

from allauth.mfa.models import Authenticator
from allauth.mfa.utils import is_mfa_enabled
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

# The two MFA views live outside "/admin/" (accounts/urls.py, mounted at the
# URL root) specifically so admin.site.urls's own catch-all can never shadow
# them — so this gate never needs to exempt them by path.


class AdminMfaMiddleware:
    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if self._needs_gate(request):
            user = request.user
            if not is_mfa_enabled(user, [Authenticator.Type.TOTP]):
                return redirect("accounts:admin_mfa_enroll")
            if not request.session.get("admin_mfa_verified"):
                return redirect("accounts:admin_mfa_challenge")
        return self.get_response(request)

    def _needs_gate(self, request: HttpRequest) -> bool:
        if not request.path.startswith("/admin/"):
            return False
        user = request.user
        return user.is_authenticated and user.is_staff
