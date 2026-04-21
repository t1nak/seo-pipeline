"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-21

Creates all tables for the seo_pipeline schema: run_log, gsc_performance_daily,
gsc_indexation_snapshot, sitemap_probe, redirect_probe, recovery_metrics_weekly,
alerts. Confined to the seo_pipeline schema — no changes to public or any
eraluma-owned schema.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

SCHEMA = "seo_pipeline"


def upgrade() -> None:
    op.execute(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA}"')

    op.create_table(
        "run_log",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("run_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("run_finished_at", sa.DateTime(timezone=True)),
        sa.Column("job_name", sa.Text, nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("error_message", sa.Text),
        sa.Column("rows_written", sa.Integer),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_run_log_started_at", "run_log", ["run_started_at"], schema=SCHEMA
    )
    op.create_index("ix_run_log_job", "run_log", ["job_name"], schema=SCHEMA)

    op.create_table(
        "gsc_performance_daily",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("domain", sa.Text, nullable=False),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("query", sa.Text, nullable=False),
        sa.Column("country", sa.String(8), nullable=False),
        sa.Column("device", sa.String(16), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("clicks", sa.Integer, nullable=False, server_default="0"),
        sa.Column("impressions", sa.Integer, nullable=False, server_default="0"),
        sa.Column("ctr", sa.Float, nullable=False, server_default="0"),
        sa.Column("position", sa.Float, nullable=False, server_default="0"),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "domain", "url", "query", "date", "country", "device",
            name="uq_gsc_performance_daily",
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_gsc_performance_daily_date", "gsc_performance_daily", ["date"], schema=SCHEMA
    )
    op.create_index(
        "ix_gsc_performance_daily_url", "gsc_performance_daily", ["url"], schema=SCHEMA
    )

    op.create_table(
        "gsc_indexation_snapshot",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("domain", sa.Text, nullable=False),
        sa.Column("coverage_state", sa.Text, nullable=False),
        sa.Column("url_count", sa.Integer, nullable=False),
        sa.Column("snapshot_date", sa.Date, nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "domain", "coverage_state", "snapshot_date",
            name="uq_gsc_indexation_snapshot",
        ),
        schema=SCHEMA,
    )

    op.create_table(
        "sitemap_probe",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("locale", sa.String(8)),
        sa.Column("url_type", sa.Text, nullable=False),
        sa.Column("blogpost_id", sa.Integer),
        sa.Column("probed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("http_status", sa.Integer),
        sa.Column("response_time_ms", sa.Integer),
        sa.Column("has_noindex", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("canonical_url", sa.Text),
        sa.Column(
            "canonical_matches_self", sa.Boolean, nullable=False, server_default=sa.false()
        ),
        sa.Column("hreflang_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("title", sa.Text),
        sa.Column("meta_description", sa.Text),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_sitemap_probe_probed_at", "sitemap_probe", ["probed_at"], schema=SCHEMA
    )
    op.create_index("ix_sitemap_probe_url", "sitemap_probe", ["url"], schema=SCHEMA)
    op.create_index(
        "ix_sitemap_probe_url_type", "sitemap_probe", ["url_type"], schema=SCHEMA
    )

    op.create_table(
        "redirect_probe",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("old_url", sa.Text, nullable=False),
        sa.Column("probed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("hop_count", sa.Integer, nullable=False),
        sa.Column("chain", postgresql.JSONB, nullable=False),
        sa.Column("final_url", sa.Text),
        sa.Column("final_status", sa.Integer),
        sa.Column("cf_mitigated", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("verdict", sa.Text, nullable=False),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_redirect_probe_probed_at", "redirect_probe", ["probed_at"], schema=SCHEMA
    )
    op.create_index(
        "ix_redirect_probe_verdict", "redirect_probe", ["verdict"], schema=SCHEMA
    )

    op.create_table(
        "recovery_metrics_weekly",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("week_start", sa.Date, nullable=False),
        sa.Column("baseline_daily_clicks", sa.Float, nullable=False, server_default="0"),
        sa.Column(
            "baseline_daily_impressions", sa.Float, nullable=False, server_default="0"
        ),
        sa.Column("current_daily_clicks", sa.Float, nullable=False, server_default="0"),
        sa.Column(
            "current_daily_impressions", sa.Float, nullable=False, server_default="0"
        ),
        sa.Column("clicks_recovery_ratio", sa.Float, nullable=False, server_default="0"),
        sa.Column(
            "impressions_recovery_ratio", sa.Float, nullable=False, server_default="0"
        ),
        sa.Column(
            "anchor_blogpost_weekly_clicks", sa.Integer, nullable=False, server_default="0"
        ),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("week_start", name="uq_recovery_metrics_weekly_week"),
        schema=SCHEMA,
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("severity", sa.Text, nullable=False),
        sa.Column("job_name", sa.Text, nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column(
            "run_log_id",
            sa.BigInteger,
            sa.ForeignKey(f"{SCHEMA}.run_log.id"),
        ),
        schema=SCHEMA,
    )
    op.create_index("ix_alerts_created_at", "alerts", ["created_at"], schema=SCHEMA)
    op.create_index("ix_alerts_resolved_at", "alerts", ["resolved_at"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_index("ix_alerts_resolved_at", table_name="alerts", schema=SCHEMA)
    op.drop_index("ix_alerts_created_at", table_name="alerts", schema=SCHEMA)
    op.drop_table("alerts", schema=SCHEMA)
    op.drop_table("recovery_metrics_weekly", schema=SCHEMA)
    op.drop_index("ix_redirect_probe_verdict", table_name="redirect_probe", schema=SCHEMA)
    op.drop_index("ix_redirect_probe_probed_at", table_name="redirect_probe", schema=SCHEMA)
    op.drop_table("redirect_probe", schema=SCHEMA)
    op.drop_index("ix_sitemap_probe_url_type", table_name="sitemap_probe", schema=SCHEMA)
    op.drop_index("ix_sitemap_probe_url", table_name="sitemap_probe", schema=SCHEMA)
    op.drop_index("ix_sitemap_probe_probed_at", table_name="sitemap_probe", schema=SCHEMA)
    op.drop_table("sitemap_probe", schema=SCHEMA)
    op.drop_table("gsc_indexation_snapshot", schema=SCHEMA)
    op.drop_index(
        "ix_gsc_performance_daily_url", table_name="gsc_performance_daily", schema=SCHEMA
    )
    op.drop_index(
        "ix_gsc_performance_daily_date", table_name="gsc_performance_daily", schema=SCHEMA
    )
    op.drop_table("gsc_performance_daily", schema=SCHEMA)
    op.drop_index("ix_run_log_job", table_name="run_log", schema=SCHEMA)
    op.drop_index("ix_run_log_started_at", table_name="run_log", schema=SCHEMA)
    op.drop_table("run_log", schema=SCHEMA)
