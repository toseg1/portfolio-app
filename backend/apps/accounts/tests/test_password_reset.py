from unittest.mock import patch

import pytest
from django.test import Client

from apps.notifications.models import EmailLog

from .factories import make_user
from .helpers import get_csrf, post_json

pytestmark = pytest.mark.django_db


class TestPasswordReset:
    def test_request_for_existing_email_queues_email(self):
        make_user(email="user@example.com")
        client = Client(enforce_csrf_checks=True)
        csrf_token = get_csrf(client)

        with patch("apps.notifications.services.send_queued_email") as mock_task:
            response = post_json(
                client, "/api/v1/auth/password/request", {"email": "user@example.com"}, csrf_token
            )

        assert response.status_code == 200
        mock_task.delay.assert_called_once()
        assert EmailLog.objects.filter(
            template_key="auth.password_reset", recipient_email="user@example.com"
        ).exists()

    def test_request_for_unknown_email_looks_identical_from_the_api(self):
        client = Client(enforce_csrf_checks=True)
        csrf_token = get_csrf(client)
        known_client = Client(enforce_csrf_checks=True)
        known_csrf = get_csrf(known_client)
        make_user(email="known@example.com")

        with patch("apps.notifications.services.send_queued_email") as mock_unknown:
            unknown_response = post_json(
                client, "/api/v1/auth/password/request", {"email": "nobody@example.com"}, csrf_token
            )
        with patch("apps.notifications.services.send_queued_email") as mock_known:
            known_response = post_json(
                known_client,
                "/api/v1/auth/password/request",
                {"email": "known@example.com"},
                known_csrf,
            )

        # Identical response either way (just {"status": 200}, no "data") —
        # no account enumeration via the HTTP response. Internally, each
        # queues its own email (a real reset link vs. a "you don't have an
        # account yet" notice) — only the account holder ever sees which.
        assert unknown_response.status_code == known_response.status_code == 200
        assert unknown_response.json() == known_response.json()
        mock_unknown.delay.assert_called_once()
        mock_known.delay.assert_called_once()
        assert EmailLog.objects.get(recipient_email="nobody@example.com").template_key == (
            "auth.unknown_account"
        )
        assert EmailLog.objects.get(recipient_email="known@example.com").template_key == (
            "auth.password_reset"
        )

    def test_reset_with_valid_key_changes_password(self):
        user = make_user(email="user@example.com", password="old-correct-password")
        client = Client(enforce_csrf_checks=True)
        csrf_token = get_csrf(client)

        captured = {}

        def _capture(**kwargs):
            captured.update(kwargs)
            return EmailLog.objects.create(
                recipient_email=kwargs["recipient_email"],
                category=kwargs["category"],
                template_key=kwargs["template_key"],
                template_version=kwargs["template_version"],
                language=kwargs["language"],
                sender_role=kwargs["sender_role"],
                from_email="hello@example.invalid",
                subject=kwargs["subject"],
            )

        with patch("apps.accounts.adapters.queue_email", side_effect=_capture):
            post_json(
                client, "/api/v1/auth/password/request", {"email": "user@example.com"}, csrf_token
            )

        key = captured["context"]["url"].rstrip("/").rsplit("/", 1)[-1]

        response = post_json(
            client,
            "/api/v1/auth/password/reset",
            {"key": key, "password": "brand-new-correct-password"},
            csrf_token,
        )

        # Resetting the password doesn't auto-authenticate the headless
        # session — 401 ("please login") is the expected success shape here,
        # distinct from the 400 an invalid/garbage key gets below.
        assert response.status_code == 401
        user.refresh_from_db()
        assert user.check_password("brand-new-correct-password")

    def test_reset_with_invalid_key_rejected(self):
        make_user(email="user@example.com")
        client = Client(enforce_csrf_checks=True)
        csrf_token = get_csrf(client)

        response = post_json(
            client,
            "/api/v1/auth/password/reset",
            {"key": "not-a-real-key", "password": "brand-new-correct-password"},
            csrf_token,
        )

        assert response.status_code == 400
