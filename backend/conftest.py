import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clear_cache():
    """Redis-backed CACHES persists across separate test *runs* (unlike the
    Postgres test database, torn down and recreated each session) — without
    this, allauth's own rate limiting (django.core.cache-based) leaks state
    between runs and makes tests that hit it flaky/order-dependent.
    """
    cache.clear()
    yield
    cache.clear()
