"""Custom UserAdmin — can't subclass `django.contrib.auth.admin.UserAdmin`
directly, it assumes a username field this User model doesn't have.
"""

from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import User


class AccountsUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email",)


class AccountsUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("email", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    add_form = AccountsUserCreationForm
    form = AccountsUserChangeForm
    model = User

    list_display = ("email", "is_active", "is_staff", "is_superuser", "created_at")
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("email",)
    ordering = ("email",)
    readonly_fields = ("created_at", "updated_at", "last_login")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = ((None, {"fields": ("email", "password1", "password2")}),)
