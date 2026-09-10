import pytest

from apps.notifications.senders import resolve_sender


@pytest.fixture(autouse=True)
def email_settings(settings):
    settings.EMAIL_FROM_SYSTEM = "Portfolio App <hello@example.invalid>"
    settings.EMAIL_FROM_ADVISORY = "Theo <theo@example.invalid>"
    settings.EMAIL_REPLY_TO = "hello@example.invalid"
    settings.EMAIL_OPERATOR_ALERTS = "ops@example.invalid"


def test_system_role():
    sender = resolve_sender("SYSTEM")
    assert sender.from_email == "Portfolio App <hello@example.invalid>"
    assert sender.reply_to == "hello@example.invalid"


def test_advisory_role():
    sender = resolve_sender("ADVISORY")
    assert sender.from_email == "Theo <theo@example.invalid>"
    assert sender.reply_to == "hello@example.invalid"


def test_operator_alerts_role_has_no_reply_to():
    sender = resolve_sender("OPERATOR_ALERTS")
    assert sender.from_email == "ops@example.invalid"
    assert sender.reply_to is None


def test_unknown_role_raises():
    with pytest.raises(ValueError):
        resolve_sender("MARKETING")
