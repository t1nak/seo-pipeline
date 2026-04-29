"""Shared pytest fixtures for the pipeline tests."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Make the repo root importable as `src.*`
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def reset_settings_singleton(monkeypatch):
    """Reset the lazy `settings` singleton between tests so env overrides apply.

    Pydantic Settings caches values at import; tests that monkey-patch env
    vars need a fresh `Settings()` instance to see them.
    """
    # Clear any PIPELINE_* env vars that could leak between tests.
    for key in list(os.environ):
        if key.startswith("PIPELINE_"):
            monkeypatch.delenv(key, raising=False)
    yield
