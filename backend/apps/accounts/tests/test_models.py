import pytest
from django.db import IntegrityError, transaction

from apps.accounts.models import User

from .factories import make_user

pytestmark = pytest.mark.django_db


class TestUser:
    def test_email_is_the_username_field(self):
        assert User.USERNAME_FIELD == "email"
        assert User.REQUIRED_FIELDS == []
        assert not hasattr(User, "username")

    def test_email_unique_case_insensitive(self):
        make_user(email="user@example.com")
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                make_user(email="User@Example.com")

    def test_create_user_hashes_password(self):
        user = make_user(email="plain@example.com", password="s3cret-password")
        assert user.password != "s3cret-password"
        assert user.check_password("s3cret-password")

    def test_create_user_defaults_to_non_staff_non_superuser(self):
        user = make_user()
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.is_active is True

    def test_create_superuser_sets_staff_and_superuser(self):
        user = User.objects.create_superuser(email="admin@example.com", password="s3cret-password")
        assert user.is_staff is True
        assert user.is_superuser is True
