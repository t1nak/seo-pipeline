"""Derived weekly summary of migration recovery.

Compares post-migration traffic on capetowndata.com to the pre-migration
baseline on es-capetown.com and writes a single row per ISO week to
recovery_metrics_weekly.

If the underlying GSC tables are empty (because gsc_performance hasn't been
wired yet), the job writes a row with zeros so the dashboard has something to
render. Once GSC is wired, the same row gets upserted with real numbers.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.dialects.postgresql import insert

from ..config import (
    LEGACY_DOMAIN,
    LOCALES,
    MIGRATION_DATE,
    PRIMARY_DOMAIN,
    TRAFFIC_ANCHOR_BLOGPOST_ID,
)
from ..models import GscPerformanceDaily, RecoveryMetricsWeekly
from ._runlog import JobContext, raise_alert, run_job

logger = logging.getLogger(__name__)

BASELINE_WINDOW_DAYS = 90


def _migration_date() -> date:
    return date.fromisoformat(MIGRATION_DATE)


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _fetch_daily_average(
    ctx: JobContext, domain: str, start: date, end: date
) -> tuple[float, float]:
    """Return (avg_daily_clicks, avg_daily_impressions) over [start, end)."""
    # Sum clicks/impressions over the window, then divide by number of days.
    stmt = select(
        func.coalesce(func.sum(GscPerformanceDaily.clicks), 0),
        func.coalesce(func.sum(GscPerformanceDaily.impressions), 0),
    ).where(
        and_(
            GscPerformanceDaily.domain == domain,
            GscPerformanceDaily.date >= start,
            GscPerformanceDaily.date < end,
        )
    )
    total_clicks, total_impressions = ctx.session.execute(stmt).one()
    days = max((end - start).days, 1)
    return float(total_clicks) / days, float(total_impressions) / days


def _anchor_weekly_clicks(
    ctx: JobContext, week_start: date, week_end: date
) -> int:
    """Sum clicks on blogpost 140 across all 9 locale variants for the week."""
    anchor_urls = [
        f"https://{PRIMARY_DOMAIN}/{lang}/products/blogpost/{TRAFFIC_ANCHOR_BLOGPOST_ID}/"
        for lang in LOCALES
    ]
    stmt = select(func.coalesce(func.sum(GscPerformanceDaily.clicks), 0)).where(
        and_(
            GscPerformanceDaily.domain == PRIMARY_DOMAIN,
            GscPerformanceDaily.url.in_(anchor_urls),
            GscPerformanceDaily.date >= week_start,
            GscPerformanceDaily.date < week_end,
        )
    )
    return int(ctx.session.execute(stmt).scalar() or 0)


def _check_declining_ratio(ctx: JobContext) -> None:
    """Warn if the clicks recovery ratio has declined for 2 consecutive weeks."""
    recent = ctx.session.execute(
        select(RecoveryMetricsWeekly.week_start, RecoveryMetricsWeekly.clicks_recovery_ratio)
        .order_by(RecoveryMetricsWeekly.week_start.desc())
        .limit(3)
    ).all()
    if len(recent) < 3:
        return
    latest, mid, oldest = recent
    if latest.clicks_recovery_ratio < mid.clicks_recovery_ratio < oldest.clicks_recovery_ratio:
        raise_alert(
            ctx,
            severity="warning",
            message=(
                f"Clicks recovery ratio declining for 2 consecutive weeks: "
                f"{oldest.clicks_recovery_ratio:.2f} → "
                f"{mid.clicks_recovery_ratio:.2f} → "
                f"{latest.clicks_recovery_ratio:.2f}."
            ),
        )


def compute_for_week(ctx: JobContext, week_start: date) -> RecoveryMetricsWeekly:
    week_end = week_start + timedelta(days=7)
    migration = _migration_date()

    baseline_start = migration - timedelta(days=BASELINE_WINDOW_DAYS)
    baseline_end = migration
    b_clicks, b_impr = _fetch_daily_average(
        ctx, LEGACY_DOMAIN, baseline_start, baseline_end
    )

    c_clicks, c_impr = _fetch_daily_average(
        ctx, PRIMARY_DOMAIN, week_start, week_end
    )

    clicks_ratio = (c_clicks / b_clicks) if b_clicks > 0 else 0.0
    impr_ratio = (c_impr / b_impr) if b_impr > 0 else 0.0

    anchor_clicks = _anchor_weekly_clicks(ctx, week_start, week_end)

    stmt = insert(RecoveryMetricsWeekly).values(
        week_start=week_start,
        baseline_daily_clicks=b_clicks,
        baseline_daily_impressions=b_impr,
        current_daily_clicks=c_clicks,
        current_daily_impressions=c_impr,
        clicks_recovery_ratio=clicks_ratio,
        impressions_recovery_ratio=impr_ratio,
        anchor_blogpost_weekly_clicks=anchor_clicks,
        computed_at=datetime.now(timezone.utc),
    )
    stmt = stmt.on_conflict_do_update(
        constraint="uq_recovery_metrics_weekly_week",
        set_={
            "baseline_daily_clicks": stmt.excluded.baseline_daily_clicks,
            "baseline_daily_impressions": stmt.excluded.baseline_daily_impressions,
            "current_daily_clicks": stmt.excluded.current_daily_clicks,
            "current_daily_impressions": stmt.excluded.current_daily_impressions,
            "clicks_recovery_ratio": stmt.excluded.clicks_recovery_ratio,
            "impressions_recovery_ratio": stmt.excluded.impressions_recovery_ratio,
            "anchor_blogpost_weekly_clicks": stmt.excluded.anchor_blogpost_weekly_clicks,
            "computed_at": stmt.excluded.computed_at,
        },
    )
    ctx.session.execute(stmt)

    # Return a dict-like view for testing
    return RecoveryMetricsWeekly(
        week_start=week_start,
        baseline_daily_clicks=b_clicks,
        baseline_daily_impressions=b_impr,
        current_daily_clicks=c_clicks,
        current_daily_impressions=c_impr,
        clicks_recovery_ratio=clicks_ratio,
        impressions_recovery_ratio=impr_ratio,
        anchor_blogpost_weekly_clicks=anchor_clicks,
        computed_at=datetime.now(timezone.utc),
    )


def run() -> None:
    with run_job("recovery_metrics") as ctx:
        today = date.today()
        ws = _week_start(today - timedelta(days=7))  # last full week
        compute_for_week(ctx, ws)
        ctx.rows_written = 1
        _check_declining_ratio(ctx)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
