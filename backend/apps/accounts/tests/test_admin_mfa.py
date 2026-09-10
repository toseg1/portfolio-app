import time

import pytest
from allauth.mfa import app_settings as mfa_app_settings
from allauth.mfa.totp.internal.auth import SECRET_SESSION_KEY, format_hotp_value, hotp_value
from django.test import Client

from apps.accounts.models import User

from .factories import make_user

pytestmark = pytest.mark.django_db


def _current_code(secret: str) -> str:
    counter = int(time.time()) // mfa_app_settings.TOTP_PERIOD
    return format_hotp_value(hotp_value(secret, counter))


def _make_staff(email: str, password: str) -> User:
    user = make_user(email=email, password=password)
    user.is_staff = True
    user.save(update_fields=["is_staff"])
    return user


def _admin_login(client: Client, email: str, password: str):
    return client.post("/admin/login/", {"username": email, "password": password})


class TestAdminMfaGate:
    def test_staff_without_totp_is_redirected_to_enroll(self):
        _make_staff("staff@example.com", "correct-horse-battery-staple")
        client = Client()
        _admin_login(client, "staff@example.com", "correct-horse-battery-staple")

        response = client.get("/admin/")

        assert response.status_code == 302
        assert response["Location"] == "/staff-mfa/enroll/"

    def test_non_staff_login_never_reaches_admin(self):
        make_user(email="plain@example.com", password="correct-horse-battery-staple")
        client = Client()
        response = _admin_login(client, "plain@example.com", "correct-horse-battery-staple")

        # Django admin's own login view rejects non-staff before our
        # middleware is ever relevant.
        assert response.status_code == 200
        admin_index = client.get("/admin/")
        assert admin_index.status_code in (302, 403)

    def test_staff_with_totp_but_unverified_session_is_challenged(self):
        _make_staff("staff2@example.com", "correct-horse-battery-staple")
        client = Client()
        _admin_login(client, "staff2@example.com", "correct-horse-battery-staple")

        enroll_get = client.get("/staff-mfa/enroll/")
        assert enroll_get.status_code == 200
        secret = client.session[SECRET_SESSION_KEY]
        client.post("/staff-mfa/enroll/", {"code": _current_code(secret)})

        # New client session: TOTP exists, but this session hasn't verified yet.
        second_client = Client()
        _admin_login(second_client, "staff2@example.com", "correct-horse-battery-staple")
        response = second_client.get("/admin/")

        assert response.status_code == 302
        assert response["Location"] == "/staff-mfa/challenge/"

    def test_staff_completes_challenge_and_reaches_admin(self):
        _make_staff("staff3@example.com", "correct-horse-battery-staple")
        client = Client()
        _admin_login(client, "staff3@example.com", "correct-horse-battery-staple")
        client.get("/staff-mfa/enroll/")
        secret = client.session[SECRET_SESSION_KEY]
        client.post("/staff-mfa/enroll/", {"code": _current_code(secret)})

        second_client = Client()
        _admin_login(second_client, "staff3@example.com", "correct-horse-battery-staple")
        second_client.get("/admin/")  # redirected to challenge, primes the form
        response = second_client.post(
            "/staff-mfa/challenge/", {"code": _current_code(secret)}
        )

        assert response.status_code == 302
        assert response["Location"] == "/admin/"
        admin_index = second_client.get("/admin/")
        assert admin_index.status_code == 200

    def test_superuser_gets_no_bypass(self):
        user = make_user(email="root@example.com", password="correct-horse-battery-staple")
        user.is_staff = True
        user.is_superuser = True
        user.save(update_fields=["is_staff", "is_superuser"])
        client = Client()
        _admin_login(client, "root@example.com", "correct-horse-battery-staple")

        response = client.get("/admin/")

        assert response.status_code == 302
        assert response["Location"] == "/staff-mfa/enroll/"
