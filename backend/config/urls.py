"""Auth endpoints are allauth's own `allauth.headless` "browser"-client views,
mounted under /api/v1/ ourselves (build_urlpatterns(Client.BROWSER) from each
submodule) rather than via `include("allauth.headless.urls")`, which hardcodes
a browser/v1/ prefix — same views, same security, this repo's own URL
convention instead of allauth's default one.
"""

from allauth.headless.account import urls as headless_account_urls
from allauth.headless.base import urls as headless_base_urls
from allauth.headless.constants import Client
from allauth.headless.mfa import urls as headless_mfa_urls
from django.contrib import admin
from django.urls import include, path

api_v1_patterns = (
    headless_base_urls.build_urlpatterns(Client.BROWSER)
    + headless_account_urls.build_urlpatterns(Client.BROWSER)
    + headless_mfa_urls.build_urlpatterns(Client.BROWSER)
)

urlpatterns: list = [
    path("admin/", admin.site.urls),
    path("", include("apps.accounts.urls")),
    path("api/v1/", include(api_v1_patterns)),
]
