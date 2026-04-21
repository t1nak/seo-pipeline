"""Snapshot index coverage counts per property, per coverage_state.

Scaffolded: the GSC URL Inspection / Index Coverage API calls are stubbed
with TODO markers. Persist path is live.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Iterable

from sqlalchemy.dialects.postgresql import insert

from ..config import GSC_PROPERTIES
from ..models import GscIndexationSnapshot
from ._runlog import JobContext, raise_alert, run_job

logger = logging.getLogger(__name__)


TRACKED_COVERAGE_STATES = (
    "Indexed",
    "Crawled - currently not indexed",
    "Discovered - currently not indexed",
    "Page with redirect",
    "Duplicate without user-selected canonical",
    "Blocked by robots.txt",
    "Not found (404)",
    "Redirect error",
    "Server error (5xx)",
)


def _fetch_coverage_for_property(property_uri: str) -> Iterable[dict]:
    """Yield {coverage_state, url_count} rows for a property.

    TODO(creds-wired): the Search Console v1 API doesn't expose Coverage in a
    single listing — we'll need to combine URL Inspection API calls with the
    sitemap URLs to compute per-state counts, or use the Inspection export if
    available. Stub returns nothing until that's implemented.
    """
    logger.warning(
        "gsc_indexation: coverage fetch not yet wired — returning no rows for %s",
        property_uri,
    )
    return []


def _property_uri_to_domain(uri: str) -> str:
    if uri.startswith("sc-domain:"):
        return uri[len("sc-domain:"):]
    return uri


def _persist(ctx: JobContext, property_uri: str, rows: Iterable[dict]) -> int:
    domain = _property_uri_to_domain(property_uri)
    snapshot_date = date.today()
    now = datetime.now(timezone.utc)
    count = 0
    for row in rows:
        stmt = insert(GscIndexationSnapshot).values(
            domain=domain,
            coverage_state=row["coverage_state"],
            url_count=row["url_count"],
            snapshot_date=snapshot_date,
            fetched_at=now,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_gsc_indexation_snapshot",
            set_={
                "url_count": stmt.excluded.url_count,
                "fetched_at": stmt.excluded.fetched_at,
            },
        )
        ctx.session.execute(stmt)
        count += 1
    return count


def _check_indexed_drop(ctx: JobContext) -> None:
    """Warn if Indexed count on capetowndata.com dropped week-over-week
    during recovery phase."""
    from sqlalchemy import select, and_
    from ..models import GscIndexationSnapshot as GIS

    domain = "capetowndata.com"
    recent = ctx.session.execute(
        select(GIS.snapshot_date, GIS.url_count)
        .where(and_(GIS.domain == domain, GIS.coverage_state == "Indexed"))
        .order_by(GIS.snapshot_date.desc())
        .limit(8)
    ).all()
    if len(recent) < 2:
        return
    latest = recent[0].url_count
    prior = recent[-1].url_count
    if prior > 0 and latest < prior:
        raise_alert(
            ctx,
            severity="warning",
            message=(
                f"Indexed count on {domain} dropped: prior snapshot {prior}, "
                f"latest {latest}. Recovery-phase indexation should only grow."
            ),
        )


def run() -> None:
    with run_job("gsc_indexation") as ctx:
        total = 0
        for prop in GSC_PROPERTIES:
            rows = _fetch_coverage_for_property(prop)
            total += _persist(ctx, prop, rows)
        ctx.rows_written = total
        _check_indexed_drop(ctx)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
