"""Thin wrapper around the Google Search Console API.

Service account credentials load from GSC_SERVICE_ACCOUNT_JSON_PATH. In CI the
env var GSC_SERVICE_ACCOUNT_JSON (the raw JSON) is written to a tempfile by
the workflow before the pipeline runs.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from google.oauth2 import service_account
from googleapiclient.discovery import build

from ..config import load_settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


@lru_cache(maxsize=1)
def get_gsc_service():
    settings = load_settings()
    if settings.gsc_service_account_path is None:
        raise RuntimeError(
            "GSC_SERVICE_ACCOUNT_JSON_PATH not set — cannot authenticate with GSC API."
        )
    if not settings.gsc_service_account_path.exists():
        raise RuntimeError(
            f"GSC service account file not found at {settings.gsc_service_account_path}"
        )

    credentials = service_account.Credentials.from_service_account_file(
        str(settings.gsc_service_account_path), scopes=SCOPES
    )
    return build("searchconsole", "v1", credentials=credentials, cache_discovery=False)
