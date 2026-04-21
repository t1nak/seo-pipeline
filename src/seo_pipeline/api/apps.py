"""Django AppConfig for the dashboard."""

from __future__ import annotations

from django.apps import AppConfig


class SeoPipelineDashboardConfig(AppConfig):
    name = "seo_pipeline.api"
    label = "seo_pipeline_dashboard"
    verbose_name = "SEO Pipeline Dashboard"
