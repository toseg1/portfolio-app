from django.urls import path

from . import admin_views

app_name = "accounts"

urlpatterns = [
    path("staff-mfa/enroll/", admin_views.admin_mfa_enroll, name="admin_mfa_enroll"),
    path("staff-mfa/challenge/", admin_views.admin_mfa_challenge, name="admin_mfa_challenge"),
]
