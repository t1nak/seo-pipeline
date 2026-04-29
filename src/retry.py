"""Retry decorator for transient API failures.

Stdlib only. Wraps a function call so that it gets retried with
exponential backoff when the function raises an error class that the
caller marked as retryable.

Why a custom decorator instead of `tenacity`:

  * No extra runtime dependency.
  * Total surface area is ~70 lines, easy to read in a code review.
  * The behaviour we need (exponential backoff with jitter, optional
    `Retry-After` honor, hook into our logger) is straightforward.
  * The decorator is pure function composition, no class state, so
    it composes well with the provider classes in `brief.py`.

Usage:

    from src.retry import with_retry, retryable_default

    @with_retry(retryable=retryable_default)
    def call_api(...):
        return client.messages.create(...)

The default `retryable_default` matcher catches the standard transient
classes from the Anthropic and OpenAI SDKs (Rate-Limit, Timeout,
Connection, 5xx Status) without importing those SDKs at module load
time, so this module stays SDK-agnostic.
"""
from __future__ import annotations

import functools
import logging
import random
import time
from typing import Callable, TypeVar

from src.config import settings

logger = logging.getLogger(__name__)


T = TypeVar("T")


# Class-name patterns that count as transient on the Anthropic and
# OpenAI SDKs. Matched as substrings against the exception class name to
# avoid hard imports.
_TRANSIENT_CLASS_PATTERNS = (
    "RateLimitError",
    "APITimeoutError",
    "APIConnectionError",
    "APIError",                # OpenAI generic
    "InternalServerError",
    "ServiceUnavailableError",
    "OverloadedError",         # Anthropic
)


def retryable_default(exc: BaseException) -> bool:
    """Return True if `exc` is a class we should retry on transient grounds.

    Matches by class name to keep this module SDK-agnostic. Also retries
    on plain `TimeoutError` and `ConnectionError` from stdlib.
    """
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True
    cls = type(exc).__name__
    return any(p in cls for p in _TRANSIENT_CLASS_PATTERNS)


def _retry_after_seconds(exc: BaseException) -> float | None:
    """If the exception carries a Retry-After header, return that as seconds.

    Both Anthropic and OpenAI SDK errors expose a `response` attribute with
    `headers`. We read `Retry-After`, which is the standard hint.
    """
    response = getattr(exc, "response", None)
    if response is None:
        return None
    headers = getattr(response, "headers", None) or {}
    raw = headers.get("Retry-After") or headers.get("retry-after")
    if not raw:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def with_retry(
    retryable: Callable[[BaseException], bool] = retryable_default,
    max_attempts: int | None = None,
    base_delay: float | None = None,
    max_delay: float | None = None,
    multiplier: float | None = None,
    jitter: float = 0.25,
):
    """Decorator: retry the wrapped call on transient failures.

    All numeric parameters fall back to `src.config.settings.brief_retry_*`
    if not provided, which themselves fall back to env vars and defaults.
    Means a deployment can re-tune retry behaviour without code change.

    Args:
        retryable: predicate over exceptions; True => retry, False => raise.
        max_attempts, base_delay, max_delay, multiplier, jitter: standard
            exponential-backoff parameters with jitter as a fraction of the
            delay (so jitter=0.25 means +/-25 percent random noise).
    """
    max_attempts = max_attempts or settings.brief_retry_max_attempts
    base_delay = base_delay if base_delay is not None else settings.brief_retry_base_delay
    max_delay = max_delay if max_delay is not None else settings.brief_retry_max_delay
    multiplier = multiplier if multiplier is not None else settings.brief_retry_multiplier

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> T:
            last_exc: BaseException | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except BaseException as exc:
                    last_exc = exc
                    if not retryable(exc):
                        raise
                    if attempt == max_attempts:
                        logger.error("retry exhausted after %d attempts: %s", attempt, exc)
                        raise

                    # Default exponential backoff
                    raw_delay = min(base_delay * (multiplier ** (attempt - 1)), max_delay)
                    # Honor Retry-After if present, but never sleep less than the backoff.
                    server_hint = _retry_after_seconds(exc)
                    if server_hint is not None:
                        raw_delay = max(raw_delay, server_hint)
                    # Jitter: +/-jitter percent
                    delay = raw_delay * (1.0 + random.uniform(-jitter, jitter))
                    delay = max(0.1, delay)

                    logger.warning(
                        "%s on attempt %d/%d: %s (retrying in %.1fs)",
                        type(exc).__name__, attempt, max_attempts, exc, delay,
                    )
                    time.sleep(delay)
            # Unreachable; the loop either returns or raises.
            assert last_exc is not None
            raise last_exc

        return wrapper

    return decorator
