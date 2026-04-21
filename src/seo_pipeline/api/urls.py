"""URL routes for the SEO dashboard."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "seo_pipeline"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/alerts/<int:alert_id>/resolve/", views.resolve_alert, name="resolve_alert"),
]
