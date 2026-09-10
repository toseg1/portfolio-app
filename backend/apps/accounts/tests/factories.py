from allauth.account.models import EmailAddress

from apps.accounts.models import User


def make_user(*, verified: bool = True, **overrides):
    """Mirrors real post-signup state: a bare `User.objects.create_user()`
    has no `EmailAddress` row at all, so allauth's mandatory-verification
    gate would otherwise block login for every test user.
    """
    defaults = dict(email="user@example.com", password="correct-horse-battery-staple")
    defaults.update(overrides)
    user = User.objects.create_user(**defaults)
    EmailAddress.objects.create(
        user=user, email=user.email, primary=True, verified=verified
    )
    return user
