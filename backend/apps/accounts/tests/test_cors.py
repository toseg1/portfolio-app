import pytest
from django.test import Client

pytestmark = pytest.mark.django_db


class TestCors:
    def test_allowed_frontend_origin_gets_cors_headers(self, settings):
        settings.CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]
        client = Client()

        response = client.get("/api/v1/config", HTTP_ORIGIN="http://localhost:3000")

        assert response["Access-Control-Allow-Origin"] == "http://localhost:3000"
        assert response["Access-Control-Allow-Credentials"] == "true"

    def test_arbitrary_origin_gets_no_cors_headers(self, settings):
        settings.CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]
        client = Client()

        response = client.get("/api/v1/config", HTTP_ORIGIN="http://evil.example.com")

        assert "Access-Control-Allow-Origin" not in response
