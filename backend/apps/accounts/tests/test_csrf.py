import pytest
from django.test import Client

from .factories import make_user
from .helpers import get_csrf, post_json

pytestmark = pytest.mark.django_db


class TestCsrf:
    def test_get_sets_readable_csrf_cookie(self):
        client = Client()
        response = client.get("/api/v1/config")
        cookie = response.cookies["csrftoken"]
        assert cookie.value
        # Must stay JS-readable so the frontend api client can read it.
        assert not cookie["httponly"]

    def test_post_without_csrf_header_is_rejected(self):
        make_user(email="user@example.com", password="correct-horse-battery-staple")
        client = Client(enforce_csrf_checks=True)
        client.get("/api/v1/config")

        response = client.post(
            "/api/v1/auth/login",
            {"email": "user@example.com", "password": "correct-horse-battery-staple"},
            content_type="application/json",
        )

        assert response.status_code == 403

    def test_post_with_wrong_csrf_header_is_rejected(self):
        make_user(email="user@example.com", password="correct-horse-battery-staple")
        client = Client(enforce_csrf_checks=True)
        client.get("/api/v1/config")

        response = post_json(
            client,
            "/api/v1/auth/login",
            {"email": "user@example.com", "password": "correct-horse-battery-staple"},
            "not-the-real-token",
        )

        assert response.status_code == 403

    def test_post_with_correct_csrf_header_succeeds(self):
        make_user(email="user@example.com", password="correct-horse-battery-staple")
        client = Client(enforce_csrf_checks=True)
        csrf_token = get_csrf(client)

        response = post_json(
            client,
            "/api/v1/auth/login",
            {"email": "user@example.com", "password": "correct-horse-battery-staple"},
            csrf_token,
        )

        assert response.status_code == 200
