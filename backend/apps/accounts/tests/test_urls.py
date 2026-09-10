"""Guards the custom /api/v1/ mount (config/urls.py) against silently
reverting to allauth's own default browser/v1/ prefix on a future allauth
upgrade.
"""

import pytest
from django.urls import Resolver404, resolve

pytestmark = pytest.mark.django_db

EXPECTED_API_V1_PATHS = [
    "/api/v1/config",
    "/api/v1/auth/signup",
    "/api/v1/auth/login",
    "/api/v1/auth/session",
    "/api/v1/auth/password/request",
    "/api/v1/auth/password/reset",
    "/api/v1/auth/2fa/authenticate",
    "/api/v1/account/authenticators",
    "/api/v1/account/authenticators/totp",
    "/api/v1/account/authenticators/recovery-codes",
]


@pytest.mark.parametrize("path", EXPECTED_API_V1_PATHS)
def test_expected_path_resolves(path):
    resolve(path)


@pytest.mark.parametrize("path", ["/browser/v1/auth/login", "/app/v1/auth/login"])
def test_allauth_default_prefixes_do_not_resolve(path):
    with pytest.raises(Resolver404):
        resolve(path)


def test_staff_mfa_routes_resolve_outside_admin_prefix():
    resolve("/staff-mfa/enroll/")
    resolve("/staff-mfa/challenge/")
