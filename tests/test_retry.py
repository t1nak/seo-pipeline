"""Tests for the retry decorator in src/retry.py."""
from __future__ import annotations

import time

import pytest


def test_no_retry_on_non_retryable():
    """A ValueError is not transient. Should propagate immediately."""
    from src.retry import with_retry, retryable_default

    calls = {"n": 0}

    @with_retry(retryable=retryable_default, max_attempts=5)
    def boom():
        calls["n"] += 1
        raise ValueError("not retryable")

    with pytest.raises(ValueError):
        boom()
    assert calls["n"] == 1, "Non-retryable errors must not retry"


def test_retries_on_transient_then_succeeds(monkeypatch):
    """A retryable failure followed by success must return the success."""
    from src.retry import with_retry

    # Skip real sleeps
    monkeypatch.setattr(time, "sleep", lambda s: None)

    calls = {"n": 0}

    class FakeRateLimitError(Exception):
        pass

    @with_retry(
        retryable=lambda e: isinstance(e, FakeRateLimitError),
        max_attempts=3, base_delay=0.01, max_delay=0.05, multiplier=1.0,
    )
    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise FakeRateLimitError("transient")
        return "ok"

    assert flaky() == "ok"
    assert calls["n"] == 3, "Should have retried twice before succeeding"


def test_exhaustion_raises_last_error(monkeypatch):
    """When max_attempts is hit, the last exception must be re-raised."""
    from src.retry import with_retry

    monkeypatch.setattr(time, "sleep", lambda s: None)

    class Boom(Exception):
        pass

    @with_retry(retryable=lambda e: isinstance(e, Boom), max_attempts=3)
    def always_fails():
        raise Boom("persistent")

    with pytest.raises(Boom, match="persistent"):
        always_fails()


def test_retryable_default_matches_anthropic_class_names():
    """Default predicate catches the standard transient class names."""
    from src.retry import retryable_default

    class RateLimitError(Exception): pass
    class APITimeoutError(Exception): pass
    class APIConnectionError(Exception): pass
    class OverloadedError(Exception): pass

    assert retryable_default(RateLimitError())
    assert retryable_default(APITimeoutError())
    assert retryable_default(APIConnectionError())
    assert retryable_default(OverloadedError())

    # Stdlib transient
    assert retryable_default(TimeoutError())
    assert retryable_default(ConnectionError())

    # Non-transient
    assert not retryable_default(ValueError())
    assert not retryable_default(KeyError())
    assert not retryable_default(RuntimeError("not transient"))
