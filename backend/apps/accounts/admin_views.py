"""Staff TOTP enrolment/challenge for the Django admin MFA gate
(`middleware.AdminMfaMiddleware`). Reuses allauth's own MFA forms/flows
directly (`ActivateTOTPForm`, `ReauthenticateForm`) rather than reimplementing
TOTP crypto, QR generation or rate limiting — those forms already do all of
it, including throttling via `ACCOUNT_RATE_LIMITS["login_failed"]`.
"""

from __future__ import annotations

from allauth.mfa.adapter import get_adapter as get_mfa_adapter
from allauth.mfa.base.forms import ReauthenticateForm
from allauth.mfa.models import Authenticator
from allauth.mfa.totp.forms import ActivateTOTPForm
from allauth.mfa.totp.internal import flows as totp_flows
from allauth.mfa.utils import is_mfa_enabled
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

_staff_required = user_passes_test(lambda u: u.is_staff)


@login_required
@_staff_required
def admin_mfa_enroll(request: HttpRequest) -> HttpResponse:
    user = request.user
    if is_mfa_enabled(user, [Authenticator.Type.TOTP]):
        return redirect("accounts:admin_mfa_challenge")

    if request.method == "POST":
        form = ActivateTOTPForm(request.POST, user=user)
        if form.is_valid():
            totp_flows.activate_totp(request, form)
            request.session["admin_mfa_verified"] = True
            return redirect("admin:index")
    else:
        form = ActivateTOTPForm(user=user)

    adapter = get_mfa_adapter()
    totp_url = adapter.build_totp_url(user, form.secret)
    totp_svg = adapter.build_totp_svg(totp_url)
    return render(
        request,
        "accounts/admin_mfa_enroll.html",
        {"form": form, "totp_svg": totp_svg, "totp_url": totp_url},
    )


@login_required
@_staff_required
def admin_mfa_challenge(request: HttpRequest) -> HttpResponse:
    user = request.user
    if not is_mfa_enabled(user, [Authenticator.Type.TOTP]):
        return redirect("accounts:admin_mfa_enroll")
    if request.session.get("admin_mfa_verified"):
        return redirect("admin:index")

    if request.method == "POST":
        form = ReauthenticateForm(request.POST, user=user)
        if form.is_valid():
            form.save()
            request.session["admin_mfa_verified"] = True
            return redirect("admin:index")
    else:
        form = ReauthenticateForm(user=user)

    return render(request, "accounts/admin_mfa_challenge.html", {"form": form})
