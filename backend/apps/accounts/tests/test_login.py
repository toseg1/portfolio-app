import pytest
from django.test import Client

from .factories import make_user
from .helpers import get_csrf, post_json

pytestmark = pytest.mark.django_db


class TestLogin:
    def test_login_succeeds_with_correct_credentials(self):
        make_user(email="user@example.com", password="correct-horse-battery-staple")
        client = Client(enforce_csrf_checks=True)
        csrf_token = get_csrf(client)

        response = post_json(
            client,
            "/api/v1/auth/login",
            {"email": "user@example.com", "password": "correct-horse-battery-staple"},
            csrf_token,
        )

        body = response.json()
        assert response.status_code == 200
        assert body["meta"]["is_authenticated"] is True
        assert body["data"]["user"]["email"] == "user@example.com"

        session_cookie = response.cookies["sessionid"]
        assert session_cookie["httponly"]
        assert session_cookie["secure"]
        assert session_cookie["samesite"] == "Lax"

    def test_login_fails_with_wrong_password_generic_message(self):
        make_user(email="user@example.com", password="correct-horse-battery-staple")
        client = Client(enforce_csrf_checks=True)
        csrf_token = get_csrf(client)

        response = post_json(
            client,
            "/api/v1/auth/login",
            {"email": "user@example.com", "password": "wrong-password"},
            csrf_token,
        )

        # A rejected login is a form-validation error (ErrorResponse), not
        # an AuthenticationResponse — it carries "errors", not "meta".
        assert response.status_code == 400
        assert response.json()["errors"]

    def test_login_fails_for_unknown_email_same_shape_as_wrong_password(self):
        make_user(email="user@example.com", password="correct-horse-battery-staple")
        client = Client(enforce_csrf_checks=True)
        csrf_token = get_csrf(client)
        unknown_client = Client(enforce_csrf_checks=True)
        unknown_csrf = get_csrf(unknown_client)

        wrong_password_response = post_json(
            client,
            "/api/v1/auth/login",
            {"email": "user@example.com", "password": "whatever-password"},
            csrf_token,
        )
        unknown_email_response = post_json(
            unknown_client,
            "/api/v1/auth/login",
            {"email": "nobody@example.com", "password": "whatever-password"},
            unknown_csrf,
        )

        # No account enumeration: wrong password and unknown email produce
        # the identical response shape.
        assert wrong_password_response.status_code == unknown_email_response.status_code == 400
        assert wrong_password_response.json() == unknown_email_response.json()

    def test_logout_clears_the_session(self):
        make_user(email="user@example.com", password="correct-horse-battery-staple")
        client = Client(enforce_csrf_checks=True)
        csrf_token = get_csrf(client)
        post_json(
            client,
            "/api/v1/auth/login",
            {"email": "user@example.com", "password": "correct-horse-battery-staple"},
            csrf_token,
        )
        # Login rotates the CSRF token (allauth's own session-fixation
        # hardening) — the pre-login token is no longer valid.
        csrf_token = client.cookies["csrftoken"].value

        response = client.delete("/api/v1/auth/session", HTTP_X_CSRFTOKEN=csrf_token)

        assert response.json()["meta"]["is_authenticated"] is False

        status = client.get("/api/v1/auth/session")
        assert status.json()["meta"]["is_authenticated"] is False
