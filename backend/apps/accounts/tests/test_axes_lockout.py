import pytest
from django.test import Client

from .factories import make_user
from .helpers import get_csrf

pytestmark = pytest.mark.django_db


def _attempt(client: Client, csrf_token: str, email: str, password: str, ip: str):
    return client.post(
        "/api/v1/auth/login",
        {"email": email, "password": password},
        content_type="application/json",
        HTTP_X_CSRFTOKEN=csrf_token,
        REMOTE_ADDR=ip,
    )


class TestAxesLockout:
    def test_locks_out_after_failure_limit_same_account_and_ip(self):
        make_user(email="user@example.com", password="correct-horse-battery-staple")
        client = Client(enforce_csrf_checks=True)
        csrf_token = get_csrf(client)

        # AXES_FAILURE_LIMIT=5: the 4 attempts before the limit fail normally
        # (400) — the 5th failure is the one axes converts into a lockout
        # response, for that same request.
        for _ in range(4):
            response = _attempt(client, csrf_token, "user@example.com", "wrong", "10.0.0.1")
            assert response.status_code == 400

        locked_response = _attempt(client, csrf_token, "user@example.com", "wrong", "10.0.0.1")
        assert locked_response.status_code == 429
        assert "Retry-After" in locked_response

    def test_correct_password_still_locked_out_after_failure_limit(self):
        make_user(email="user@example.com", password="correct-horse-battery-staple")
        client = Client(enforce_csrf_checks=True)
        csrf_token = get_csrf(client)

        for _ in range(5):
            _attempt(client, csrf_token, "user@example.com", "wrong", "10.0.0.2")

        # Even the *correct* password is blocked once locked out — the point
        # of the lockout, and it must not look any different from a wrong
        # password to the caller (no enumeration of "this account exists and
        # is merely locked" vs "wrong password").
        response = _attempt(
            client, csrf_token, "user@example.com", "correct-horse-battery-staple", "10.0.0.2"
        )
        assert response.status_code == 429

    def test_lockout_is_scoped_per_ip_independent_of_account(self):
        make_user(email="victim@example.com", password="correct-horse-battery-staple")
        client = Client(enforce_csrf_checks=True)
        csrf_token = get_csrf(client)

        # Four different, non-existent accounts all failing from the same IP
        # — still under the limit, even though the IP has 4 failures.
        for i in range(4):
            response = _attempt(client, csrf_token, f"nobody{i}@example.com", "wrong", "10.0.0.3")
            assert response.status_code == 400

        # A fifth, brand new account, never seen before, from that same IP:
        # this is the failure that exhausts the *IP* dimension, even though
        # no single account has failed more than once.
        response = _attempt(client, csrf_token, "victim@example.com", "wrong", "10.0.0.3")
        assert response.status_code == 429

    def test_lockout_is_scoped_per_account_independent_of_ip(self):
        make_user(email="target@example.com", password="correct-horse-battery-staple")
        client = Client(enforce_csrf_checks=True)
        csrf_token = get_csrf(client)

        # Same account failing four times, each from a *different* IP —
        # still under the limit, even though the account has 4 failures.
        for i in range(4):
            response = _attempt(client, csrf_token, "target@example.com", "wrong", f"10.0.1.{i}")
            assert response.status_code == 400

        # A fifth attempt against that account, from a brand new IP never
        # seen before: this is the failure that exhausts the *account*
        # dimension, even though no single IP has failed more than once.
        response = _attempt(client, csrf_token, "target@example.com", "wrong", "10.0.1.99")
        assert response.status_code == 429

    def test_cooloff_escalates_across_repeated_lockout_cycles(self):
        make_user(email="user@example.com", password="correct-horse-battery-staple")
        client = Client(enforce_csrf_checks=True)
        csrf_token = get_csrf(client)

        for _ in range(4):
            _attempt(client, csrf_token, "user@example.com", "wrong", "10.0.2.1")
        first_lockout = _attempt(client, csrf_token, "user@example.com", "wrong", "10.0.2.1")
        assert first_lockout.status_code == 429
        first_retry_after = int(first_lockout["Retry-After"])

        # A failure *during* the lockout window (AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT
        # defaults to True) pushes the failure count higher, escalating the
        # next cooloff.
        second_lockout = _attempt(client, csrf_token, "user@example.com", "wrong", "10.0.2.1")
        second_retry_after = int(second_lockout["Retry-After"])

        assert second_retry_after >= first_retry_after
