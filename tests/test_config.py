"""Tests for the typed Settings class in src/config.py."""
from __future__ import annotations

import pytest


def test_defaults_are_sensible():
    """A fresh Settings() with no env vars must give the documented defaults."""
    from src.config import Settings
    s = Settings()
    assert s.discover_source == "manual"
    assert s.discover_max_keywords == 500
    assert s.enrich_provider == "estimate"
    assert s.brief_provider == "api"
    assert s.brief_model is None
    assert s.brief_max_tokens == 4096
    assert s.cluster_hdbscan_mcs == 15
    assert s.cluster_hdbscan_ms == 5
    assert s.cluster_hdbscan_method == "leaf"
    assert s.cluster_umap_neighbors == 15
    assert s.cluster_umap_random_state == 42
    assert s.log_level == "INFO"


def test_env_var_override(monkeypatch):
    """PIPELINE_BRIEF_PROVIDER=openai must override the default."""
    monkeypatch.setenv("PIPELINE_BRIEF_PROVIDER", "openai")
    monkeypatch.setenv("PIPELINE_BRIEF_MODEL", "gpt-5")
    monkeypatch.setenv("PIPELINE_DISCOVER_MAX_KEYWORDS", "300")
    monkeypatch.setenv("PIPELINE_CLUSTER_HDBSCAN_MCS", "10")
    # Disable env_file to avoid the local .env shadowing the test
    from src.config import Settings
    s = Settings(_env_file=None)
    assert s.brief_provider == "openai"
    assert s.brief_model == "gpt-5"
    assert s.discover_max_keywords == 300
    assert s.cluster_hdbscan_mcs == 10


def test_invalid_provider_rejected(monkeypatch):
    """A typo in the provider name must fail validation, not silently fall through."""
    monkeypatch.setenv("PIPELINE_BRIEF_PROVIDER", "antropic_typo")
    from src.config import Settings
    with pytest.raises(Exception):  # pydantic.ValidationError
        Settings(_env_file=None)


def test_invalid_log_level_rejected(monkeypatch):
    monkeypatch.setenv("PIPELINE_LOG_LEVEL", "TRACE_NOT_A_THING")
    from src.config import Settings
    with pytest.raises(Exception):
        Settings(_env_file=None)


def test_unrelated_env_vars_are_ignored(monkeypatch):
    """`extra=ignore` lets ANTHROPIC_API_KEY and friends coexist without error."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-not-validated")
    monkeypatch.setenv("OPENAI_API_KEY", "fake")
    from src.config import Settings
    s = Settings(_env_file=None)
    assert s.brief_provider == "api"  # untouched
