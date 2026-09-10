"""django-axes wiring for progressive-backoff login throttling (ADR-011: "per IP
and per account with progressive backoff"). allauth's own `ACCOUNT_RATE_LIMITS`
is a fixed window and stays enabled at its default — it also covers MFA-code
and recovery-code guessing (a path axes never sees, since that's not a call to
`authenticate()`). Axes adds the escalating layer specifically for the
username/password step.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from axes.helpers import get_client_ip_address
from axes.models import AccessAttempt
from django.db.models import Max, Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone

_COOLOFF_SCHEDULE_MINUTES = [1, 5, 15, 60]
_FAILURE_LOOKBACK = timedelta(hours=24)


def get_axes_username(request: HttpRequest, credentials: dict[str, Any] | None) -> str | None:
    """Django admin's form posts `username`; allauth's backend is called with
    `email=`. Both must resolve to the same lockout key so a locked-out staff
    account is locked out in both places. `credentials` is `None` on some
    internal axes call paths (e.g. resolving the cooloff threshold) that
    aren't tied to a specific login attempt.
    """
    if not credentials:
        return None
    return credentials.get("email") or credentials.get("username")


def get_cooloff(request: HttpRequest | None) -> timedelta:
    """axes calls this with `request` only — no `credentials` — to learn the
    cooloff *duration* for a request it has *already* decided is locked out
    (that decision, and the "per IP and per account" OR-of-two-dimensions
    logic, comes from AXES_LOCKOUT_PARAMETERS/AXES_FAILURE_LIMIT elsewhere,
    not from here).

    This must NOT call AxesProxyHandler.get_failures()/is_allowed() —
    axes' own failure-counting internally calls back into this exact
    function to resolve its own time window, which recurses infinitely.
    Querying AccessAttempt directly sidesteps that.
    """
    if request is None:
        return timedelta(minutes=_COOLOFF_SCHEDULE_MINUTES[0])

    ip = get_client_ip_address(request)
    username = get_axes_username(request, getattr(request, "POST", None))
    since = timezone.now() - _FAILURE_LOOKBACK

    failures = (
        AccessAttempt.objects.filter(attempt_time__gte=since)
        .filter(Q(ip_address=ip) | Q(username=username))
        .aggregate(Max("failures_since_start"))["failures_since_start__max"]
        or 0
    )
    index = min(max(failures - 1, 0), len(_COOLOFF_SCHEDULE_MINUTES) - 1)
    return timedelta(minutes=_COOLOFF_SCHEDULE_MINUTES[index])


def lockout_response(request: HttpRequest, credentials: dict[str, Any] | None) -> HttpResponse:
    """Same generic message regardless of *why* — locked by account, locked by
    IP, or (from the caller's point of view) simply still within the cooloff —
    so this never doubles as an account-enumeration or lockout-reason oracle.
    Only `Retry-After` (when, never why) is exposed.
    """
    cool_off = get_cooloff(request)
    retry_after = int(cool_off.total_seconds())

    if request.path.startswith("/admin/"):
        response = HttpResponse(
            "Too many attempts. Try again later.", status=429, content_type="text/plain"
        )
    else:
        response = JsonResponse(
            {"status": 429, "errors": [{"code": "rate_limited", "message": "Too many attempts."}]},
            status=429,
        )
    response["Retry-After"] = str(retry_after)
    return response
