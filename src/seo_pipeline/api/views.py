"""Dashboard views.

Read-only SQLAlchemy queries into the seo_pipeline schema. Kept deliberately
simple: server-rendered HTML, no SPA, no DRF. Admin-only.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from sqlalchemy import desc, func, select

from ..db import session_scope
from ..models import (
    Alert,
    RecoveryMetricsWeekly,
    RedirectProbe,
    RunLog,
    SitemapProbe,
)


@staff_member_required
def dashboard(request):
    with session_scope() as s:
        latest_recovery = s.execute(
            select(RecoveryMetricsWeekly)
            .order_by(desc(RecoveryMetricsWeekly.week_start))
            .limit(1)
        ).scalar_one_or_none()

        recovery_series = s.execute(
            select(RecoveryMetricsWeekly)
            .order_by(desc(RecoveryMetricsWeekly.week_start))
            .limit(12)
        ).scalars().all()
        recovery_series = list(reversed(recovery_series))

        # Latest redirect verdicts per old_url
        subq = (
            select(
                RedirectProbe.old_url,
                func.max(RedirectProbe.probed_at).label("last_probed"),
            )
            .group_by(RedirectProbe.old_url)
            .subquery()
        )
        latest_redirects = s.execute(
            select(RedirectProbe)
            .join(
                subq,
                (RedirectProbe.old_url == subq.c.old_url)
                & (RedirectProbe.probed_at == subq.c.last_probed),
            )
            .order_by(RedirectProbe.verdict, RedirectProbe.old_url)
        ).scalars().all()

        unresolved_alerts = s.execute(
            select(Alert)
            .where(Alert.resolved_at.is_(None))
            .order_by(desc(Alert.created_at))
        ).scalars().all()

        resolved_alerts = s.execute(
            select(Alert)
            .where(Alert.resolved_at.is_not(None))
            .order_by(desc(Alert.resolved_at))
            .limit(20)
        ).scalars().all()

        recent_runs = s.execute(
            select(RunLog).order_by(desc(RunLog.run_started_at)).limit(20)
        ).scalars().all()

        # Sitemap latest snapshot per URL for counts by type + broken list
        since = datetime.now(timezone.utc) - timedelta(days=7)
        sitemap_rows = s.execute(
            select(SitemapProbe).where(SitemapProbe.probed_at >= since)
        ).scalars().all()

    counts_by_type: dict[str, int] = {}
    broken_urls = []
    total_response_time = 0
    response_time_samples = 0
    for row in sitemap_rows:
        counts_by_type[row.url_type] = counts_by_type.get(row.url_type, 0) + 1
        if row.http_status and row.http_status >= 400:
            broken_urls.append(row)
        if row.response_time_ms is not None:
            total_response_time += row.response_time_ms
            response_time_samples += 1
    avg_response_time = (
        total_response_time / response_time_samples if response_time_samples else None
    )

    context = {
        "latest_recovery": latest_recovery,
        "recovery_series": [
            {
                "week": r.week_start.isoformat(),
                "clicks": r.current_daily_clicks,
                "impressions": r.current_daily_impressions,
                "baseline_clicks": r.baseline_daily_clicks,
                "baseline_impressions": r.baseline_daily_impressions,
                "ratio": r.clicks_recovery_ratio,
                "anchor_clicks": r.anchor_blogpost_weekly_clicks,
            }
            for r in recovery_series
        ],
        "latest_redirects": latest_redirects,
        "unresolved_alerts": unresolved_alerts,
        "resolved_alerts": resolved_alerts,
        "recent_runs": recent_runs,
        "counts_by_type": counts_by_type,
        "broken_urls": broken_urls,
        "avg_response_time_ms": avg_response_time,
    }
    return render(request, "seo_pipeline/dashboard.html", context)


@staff_member_required
def resolve_alert(request, alert_id: int):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("seo_pipeline:dashboard"))
    with session_scope() as s:
        alert = s.get(Alert, alert_id)
        if alert and alert.resolved_at is None:
            alert.resolved_at = datetime.now(timezone.utc)
    return HttpResponseRedirect(reverse("seo_pipeline:dashboard"))
