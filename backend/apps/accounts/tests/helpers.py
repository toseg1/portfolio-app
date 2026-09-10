"""allauth.headless views require a genuine JSON body — content_type=
"application/json" makes Django's test client json.dumps() the dict for us.
"""

from django.test import Client


def get_csrf(client: Client) -> str:
    client.get("/api/v1/config")
    return client.cookies["csrftoken"].value


def post_json(client: Client, path: str, data: dict, csrf_token: str, **extra):
    return client.post(
        path, data, content_type="application/json", HTTP_X_CSRFTOKEN=csrf_token, **extra
    )
