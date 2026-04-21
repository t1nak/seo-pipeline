"""Django app surface for the SEO dashboard.

The eraluma Django project can include this package in INSTALLED_APPS:

    INSTALLED_APPS = [
        ...,
        "seo_pipeline.api.apps.SeoPipelineDashboardConfig",
    ]

and wire the URLs:

    urlpatterns = [
        ...,
        path("seo/", include("seo_pipeline.api.urls")),
    ]

All views are gated by @staff_member_required. The app reads from the
seo_pipeline schema via SQLAlchemy — it does not need a Django model.
"""

default_app_config = "seo_pipeline.api.apps.SeoPipelineDashboardConfig"
