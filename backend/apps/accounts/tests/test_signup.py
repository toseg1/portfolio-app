from unittest.mock import patch

import pytest
from django.test import Client

from apps.accounts.models import User
from apps.notifications.models import EmailLog

from .factories import make_user
from .helpers import get_csrf, post_json

pytestmark = pytest.mark.django_db


class TestSignup:
    def test_signup_creates_unverified_user_and_queues_confirmation_email(self):
        client = Client(enforce_csrf_checks=True)
        csrf_token = get_csrf(client)

        with patch("apps.notifications.services.send_queued_email") as mock_task:
            response = post_json(
                client,
                "/api/v1/auth/signup",
                {"email": "new@example.com", "password": "correct-horse-battery-staple"},
                csrf_token,
            )

        assert User.objects.filter(email="new@example.com").exists()
        body = response.json()
        # Mandatory email verification: not fully authenticated yet.
        assert body["meta"]["is_authenticated"] is False

        log = EmailLog.objects.get(template_key="auth.email_confirmation")
        assert log.recipient_email == "new@example.com"
        mock_task.delay.assert_called_once()

    def test_signup_rejects_duplicate_email_without_revealing_it_exists(self):
        # A verified existing account — account_already_exists only fires
        # against a *verified* email; signing up again for a still-pending
        # unverified signup is instead treated as re-requesting verification.
        make_user(email="dupe@example.com", password="correct-horse-battery-staple")

        client = Client(enforce_csrf_checks=True)
        csrf_token = get_csrf(client)
        with patch("apps.notifications.services.send_queued_email") as mock_task:
            response = post_json(
                client,
                "/api/v1/auth/signup",
                {"email": "dupe@example.com", "password": "another-strong-password"},
                csrf_token,
            )

        # No error revealing the email is taken — allauth quietly emails the
        # existing account holder instead (account_already_exists) and
        # responds with the same shape as a genuine pending signup.
        assert response.status_code == 401
        mock_task.delay.assert_called_once()
        log = EmailLog.objects.get(template_key="auth.account_already_exists")
        assert log.recipient_email == "dupe@example.com"

    def test_signup_has_no_username_field(self):
        client = Client(enforce_csrf_checks=True)
        csrf_token = get_csrf(client)

        with patch("apps.notifications.services.send_queued_email"):
            post_json(
                client,
                "/api/v1/auth/signup",
                {
                    "email": "nouser@example.com",
                    "username": "should-be-ignored",
                    "password": "correct-horse-battery-staple",
                },
                csrf_token,
            )

        user = User.objects.get(email="nouser@example.com")
        assert not hasattr(user, "username")
