import time

import pytest
from allauth.mfa import app_settings as mfa_app_settings
from allauth.mfa.totp.internal.auth import format_hotp_value, hotp_value
from django.test import Client

from .factories import make_user
from .helpers import get_csrf, post_json

pytestmark = pytest.mark.django_db

TOTP_URL = "/api/v1/account/authenticators/totp"
LOGIN_URL = "/api/v1/auth/login"
TWO_FA_URL = "/api/v1/auth/2fa/authenticate"
EMAIL = "user@example.com"
PASSWORD = "correct-horse-battery-staple"


def _current_code(secret: str) -> str:
    counter = int(time.time()) // mfa_app_settings.TOTP_PERIOD
    return format_hotp_value(hotp_value(secret, counter))


def _login(client: Client, email: str, password: str) -> str:
    csrf_token = get_csrf(client)
    post_json(client, LOGIN_URL, {"email": email, "password": password}, csrf_token)
    return client.cookies["csrftoken"].value


def _enroll_totp(client: Client, csrf_token: str) -> str:
    secret = client.get(TOTP_URL).json()["meta"]["secret"]
    post_json(client, TOTP_URL, {"code": _current_code(secret)}, csrf_token)
    return secret


class TestTotpEnrolment:
    def test_enroll_then_login_requires_totp_code(self):
        make_user(email=EMAIL, password=PASSWORD)
        client = Client(enforce_csrf_checks=True)
        csrf_token = _login(client, EMAIL, PASSWORD)
        _enroll_totp(client, csrf_token)

        second_client = Client(enforce_csrf_checks=True)
        login_csrf = get_csrf(second_client)
        login_response = post_json(
            second_client, LOGIN_URL, {"email": EMAIL, "password": PASSWORD}, login_csrf
        )

        assert login_response.json()["meta"]["is_authenticated"] is False
        flow_ids = [f["id"] for f in login_response.json()["data"]["flows"]]
        assert "mfa_authenticate" in flow_ids

    def test_login_completes_with_correct_totp_code(self):
        make_user(email=EMAIL, password=PASSWORD)
        client = Client(enforce_csrf_checks=True)
        csrf_token = _login(client, EMAIL, PASSWORD)
        secret = _enroll_totp(client, csrf_token)

        second_client = Client(enforce_csrf_checks=True)
        login_csrf = get_csrf(second_client)
        post_json(second_client, LOGIN_URL, {"email": EMAIL, "password": PASSWORD}, login_csrf)

        code = _current_code(secret)
        totp_response = post_json(second_client, TWO_FA_URL, {"code": code}, login_csrf)

        assert totp_response.json()["meta"]["is_authenticated"] is True

    def test_login_rejects_wrong_totp_code(self):
        make_user(email=EMAIL, password=PASSWORD)
        client = Client(enforce_csrf_checks=True)
        csrf_token = _login(client, EMAIL, PASSWORD)
        _enroll_totp(client, csrf_token)

        second_client = Client(enforce_csrf_checks=True)
        login_csrf = get_csrf(second_client)
        post_json(second_client, LOGIN_URL, {"email": EMAIL, "password": PASSWORD}, login_csrf)

        totp_response = post_json(second_client, TWO_FA_URL, {"code": "000000"}, login_csrf)

        # A rejected code is a form-validation error (ErrorResponse), not an
        # AuthenticationResponse — it carries "errors", not "meta".
        assert totp_response.status_code == 400
        assert totp_response.json()["errors"]

    def test_recovery_codes_generated_on_totp_activation(self):
        make_user(email=EMAIL, password=PASSWORD)
        client = Client(enforce_csrf_checks=True)
        csrf_token = _login(client, EMAIL, PASSWORD)
        _enroll_totp(client, csrf_token)

        recovery_response = client.get("/api/v1/account/authenticators/recovery-codes")
        assert recovery_response.status_code == 200
        assert recovery_response.json()["data"]["unused_code_count"] > 0
