"""User (roadmap item 1 — auth). ADR-011: email-only login, no username.

`Client`/`Profile` (listed alongside `User` in backend/CLAUDE.md's app boundary
table) are out of scope here — they land with later roadmap items.
"""

from __future__ import annotations

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from apps.notifications.fields import CITextField

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """No username field at all — email is `USERNAME_FIELD` (confirmed with the
    user: email-only login). `last_login` stays as inherited from
    `AbstractBaseUser` — `django.contrib.auth.models.update_last_login` depends
    on that exact attribute name.
    """

    email = CITextField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        # Not "user" — a bare table name Django itself avoids for this exact
        # model (its own default is "auth_user"). Deliberate deviation from
        # copying the model name verbatim, to dodge the raw-SQL/psql footgun
        # of a table named after a near-reserved word.
        db_table = "app_user"

    def __str__(self) -> str:
        return self.email
