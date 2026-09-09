def test_django_settings_module_is_configured():
    from django.conf import settings

    assert settings.configured


def test_celery_app_is_importable():
    from config.celery import app

    assert app.main == "config"
