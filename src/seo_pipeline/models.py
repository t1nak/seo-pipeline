"""SQLAlchemy models for the seo_pipeline schema."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .config import SCHEMA_NAME


class Base(DeclarativeBase):
    metadata_schema = SCHEMA_NAME


# Apply schema to Base metadata
Base.metadata.schema = SCHEMA_NAME


class RunLog(Base):
    __tablename__ = "run_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    run_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    run_finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    job_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    rows_written: Mapped[int | None] = mapped_column(Integer)


class GscPerformanceDaily(Base):
    __tablename__ = "gsc_performance_daily"
    __table_args__ = (
        UniqueConstraint(
            "domain", "url", "query", "date", "country", "device",
            name="uq_gsc_performance_daily",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    domain: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    country: Mapped[str] = mapped_column(String(8), nullable=False)
    device: Mapped[str] = mapped_column(String(16), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    impressions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ctr: Mapped[float] = mapped_column(nullable=False, default=0.0)
    position: Mapped[float] = mapped_column(nullable=False, default=0.0)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class GscIndexationSnapshot(Base):
    __tablename__ = "gsc_indexation_snapshot"
    __table_args__ = (
        UniqueConstraint(
            "domain", "coverage_state", "snapshot_date",
            name="uq_gsc_indexation_snapshot",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    domain: Mapped[str] = mapped_column(Text, nullable=False)
    coverage_state: Mapped[str] = mapped_column(Text, nullable=False)
    url_count: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SitemapProbe(Base):
    __tablename__ = "sitemap_probe"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    locale: Mapped[str | None] = mapped_column(String(8))
    url_type: Mapped[str] = mapped_column(Text, nullable=False)
    blogpost_id: Mapped[int | None] = mapped_column(Integer)
    probed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    http_status: Mapped[int | None] = mapped_column(Integer)
    response_time_ms: Mapped[int | None] = mapped_column(Integer)
    has_noindex: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    canonical_url: Mapped[str | None] = mapped_column(Text)
    canonical_matches_self: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    hreflang_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    title: Mapped[str | None] = mapped_column(Text)
    meta_description: Mapped[str | None] = mapped_column(Text)


class RedirectProbe(Base):
    __tablename__ = "redirect_probe"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    old_url: Mapped[str] = mapped_column(Text, nullable=False)
    probed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    hop_count: Mapped[int] = mapped_column(Integer, nullable=False)
    chain: Mapped[list] = mapped_column(JSONB, nullable=False)
    final_url: Mapped[str | None] = mapped_column(Text)
    final_status: Mapped[int | None] = mapped_column(Integer)
    cf_mitigated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verdict: Mapped[str] = mapped_column(Text, nullable=False)


class RecoveryMetricsWeekly(Base):
    __tablename__ = "recovery_metrics_weekly"
    __table_args__ = (
        UniqueConstraint("week_start", name="uq_recovery_metrics_weekly_week"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    baseline_daily_clicks: Mapped[float] = mapped_column(nullable=False, default=0.0)
    baseline_daily_impressions: Mapped[float] = mapped_column(nullable=False, default=0.0)
    current_daily_clicks: Mapped[float] = mapped_column(nullable=False, default=0.0)
    current_daily_impressions: Mapped[float] = mapped_column(nullable=False, default=0.0)
    clicks_recovery_ratio: Mapped[float] = mapped_column(nullable=False, default=0.0)
    impressions_recovery_ratio: Mapped[float] = mapped_column(nullable=False, default=0.0)
    anchor_blogpost_weekly_clicks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    job_name: Mapped[str] = mapped_column(Text, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    run_log_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA_NAME}.run_log.id")
    )
