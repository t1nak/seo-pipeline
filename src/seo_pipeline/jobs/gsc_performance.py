"""Pull last-28-days performance data from GSC for both properties.

Scaffolded: the actual API-fetch loop is stubbed with TODO markers until the
service account credentials are wired in. The persist path works against real
data already — wire _fetch_rows_for_property() when creds arrive.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Iterable

from sqlalchemy.dialects.postgresql import insert

from ..config import GSC_PROPERTIES
from ..models import GscPerformanceDaily
from ._runlog import JobContext, run_job

logger = logging.getLogger(__name__)

LOOKBACK_DAYS = 28
ROW_LIMIT_PER_REQUEST = 25000


def _fetch_rows_for_property(
    property_uri: str, start: date, end: date
) -> Iterable[dict]:
    """Yield GSC API rows for a property.

    TODO(creds-wired): replace this with a real call to
    searchanalytics().query() that paginates via startRow until an empty
    response, using dimensions=[date, page, query, country, device]. Must
    respect the GSC quota (1200 QPM per project).

    Example structure of the returned dicts:
        {
          "date": "2026-04-15",
          "url": "https://capetowndata.com/en/products/blogpost/140/",
          "query": "sea point safety",
          "country": "zaf",
          "device": "MOBILE",
          "clicks": 12,
          "impressions": 340,
          "ctr": 0.035,
          "position": 4.8,
        }
    """
    logger.warning(
        "gsc_performance: GSC API call not yet wired — returning no rows for %s",
        property_uri,
    )
    return []


def _property_uri_to_domain(uri: str) -> str:
    # sc-domain:capetowndata.com → capetowndata.com
    if uri.startswith("sc-domain:"):
        return uri[len("sc-domain:"):]
    return uri


def _upsert_rows(ctx: JobContext, property_uri: str, rows: Iterable[dict]) -> int:
    domain = _property_uri_to_domain(property_uri)
    now = datetime.now(timezone.utc)
    count = 0
    for row in rows:
        stmt = insert(GscPerformanceDaily).values(
            domain=domain,
            url=row["url"],
            query=row["query"],
            country=row.get("country", ""),
            device=row.get("device", ""),
            date=row["date"],
            clicks=row.get("clicks", 0),
            impressions=row.get("impressions", 0),
            ctr=row.get("ctr", 0.0),
            position=row.get("position", 0.0),
            fetched_at=now,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_gsc_performance_daily",
            set_={
                "clicks": stmt.excluded.clicks,
                "impressions": stmt.excluded.impressions,
                "ctr": stmt.excluded.ctr,
                "position": stmt.excluded.position,
                "fetched_at": stmt.excluded.fetched_at,
            },
        )
        ctx.session.execute(stmt)
        count += 1
    return count


def run() -> None:
    with run_job("gsc_performance") as ctx:
        end = date.today()
        start = end - timedelta(days=LOOKBACK_DAYS)
        total = 0
        for prop in GSC_PROPERTIES:
            rows = _fetch_rows_for_property(prop, start, end)
            total += _upsert_rows(ctx, prop, rows)
        ctx.rows_written = total


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
