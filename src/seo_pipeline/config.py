"""Configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


GOOGLEBOT_UA = (
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
)

PRIMARY_DOMAIN = "capetowndata.com"
LEGACY_DOMAIN = "es-capetown.com"

GSC_PROPERTIES = (
    f"sc-domain:{PRIMARY_DOMAIN}",
    f"sc-domain:{LEGACY_DOMAIN}",
)

LOCALES = ("de", "en", "es", "fr", "it", "ja", "nl", "pt", "ru")

MIGRATION_DATE = "2026-02-23"

SCHEMA_NAME = "seo_pipeline"

TRAFFIC_ANCHOR_BLOGPOST_ID = 140


@dataclass(frozen=True)
class Settings:
    database_url: str
    gsc_service_account_path: Path | None
    sitemap_concurrency: int
    sitemap_rps: float


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required env var {name} is not set")
    return value


def load_settings() -> Settings:
    database_url = _require("DATABASE_URL")
    sa_path = os.environ.get("GSC_SERVICE_ACCOUNT_JSON_PATH")
    return Settings(
        database_url=database_url,
        gsc_service_account_path=Path(sa_path) if sa_path else None,
        sitemap_concurrency=int(os.environ.get("SITEMAP_CONCURRENCY", "5")),
        sitemap_rps=float(os.environ.get("SITEMAP_REQUESTS_PER_SECOND", "1.0")),
    )
