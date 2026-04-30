"""Centralised pipeline settings, loaded from environment variables.

Twelve-Factor App pattern: configuration lives in the environment, not
in source. A local `.env` file is read for development convenience, but
the primary deployment surface is real environment variables (set via
shell, Docker, Kubernetes, GitHub Actions, etc).

Precedence, highest first:
    1. CLI flags (e.g. `--brief-provider openai` on `pipeline.py`)
    2. Real environment variables (`PIPELINE_BRIEF_PROVIDER=openai`)
    3. `.env` file in the repo root
    4. Defaults defined here in `Settings`

Secrets stay outside this class. They live as plain env vars
(`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `DATAFORSEO_LOGIN`,
`DATAFORSEO_PASSWORD`, `STATICRYPT_PASSWORD`) and are read directly by
the modules that need them. This separation keeps secret values from
ever being part of a typed settings dump.

Usage:

    from src.config import settings
    print(settings.brief_provider)         # api | openai | max
    print(settings.cluster_hdbscan_mcs)    # 8
"""
from __future__ import annotations

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pipeline configuration. Every field is optional with a safe default.

    Environment variable mapping uses the prefix `PIPELINE_`, so for
    example `discover_max_keywords` is set via `PIPELINE_DISCOVER_MAX_KEYWORDS`.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="PIPELINE_",
        case_sensitive=False,
        extra="ignore",  # tolerate unrelated env vars (ANTHROPIC_API_KEY etc)
    )

    # ----- Discover -----
    discover_source: Literal["manual", "live"] = "manual"
    discover_max_keywords: int = 500

    # ----- Enrich -----
    enrich_provider: Literal["estimate", "dataforseo"] = "estimate"

    # ----- Cluster: embeddings -----
    cluster_embedding_model: str = (
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    # ----- Cluster: UMAP -----
    cluster_umap_neighbors: int = 15
    cluster_umap_random_state: int = 42
    cluster_umap_metric: str = "cosine"

    # ----- Cluster: HDBSCAN -----
    # mcs=8 sits one step below the 10-cluster plateau (mcs ∈ {10, 12, 15})
    # identified by the parameter sweep, producing more, smaller clusters
    # so that broad themes like "Zeitarbeit & Arbeitsrecht" (which dominated
    # the mcs=12 baseline at 189/500 keywords) split into more focused
    # sub-themes. Override per run via the env var
    # PIPELINE_CLUSTER_HDBSCAN_MCS or the workflow input.
    cluster_hdbscan_mcs: int = 8
    cluster_hdbscan_ms: int = 5
    cluster_hdbscan_method: Literal["eom", "leaf"] = "eom"
    cluster_hdbscan_metric: str = "euclidean"

    # ----- Brief -----
    brief_provider: Literal["api", "openai", "max"] = "api"
    brief_model: str | None = None  # None means "use the provider default"
    brief_max_tokens: int = 4096

    # ----- Brief: Retry policy on transient API errors -----
    brief_retry_max_attempts: int = 5
    brief_retry_base_delay: float = 2.0      # first backoff sleep, seconds
    brief_retry_max_delay: float = 60.0      # cap on backoff, seconds
    brief_retry_multiplier: float = 2.0      # exponential factor

    # ----- Logging -----
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"


# Module-level singleton. Import this where you need pipeline settings.
settings = Settings()
