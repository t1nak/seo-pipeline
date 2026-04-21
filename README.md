# seo-pipeline

SEO monitoring pipeline for [capetowndata.com](https://capetowndata.com) and its legacy domain `es-capetown.com` during the migration recovery window.

Runs twice weekly (Mon + Thu, 07:00 UTC), writes to a dedicated `seo_pipeline` schema on the Ceraluna Labs Postgres, and feeds an admin-only dashboard rendered by the eraluma Django app.

## Jobs

| Job | Purpose | Status |
| --- | --- | --- |
| `redirect_health` | Probe top-20 pre-migration URLs + the 18 legacy `/{lang}/products/safety/` paths. Flags any `cf-mitigated: challenge` (the pattern that broke migration for two months). | Live |
| `sitemap_crawl` | Fetch `capetowndata.com/sitemap.xml`, probe every URL, classify by shape, record status / response time / canonical / hreflang / noindex. | Live |
| `gsc_performance` | Pull last-28-day performance (clicks/impressions/CTR/position by date/page/query/country/device) for both GSC properties. | Scaffolded — persist path live, API call is a `TODO(creds-wired)` stub. |
| `gsc_indexation` | Snapshot coverage-state counts per property (Indexed / Crawled-not-indexed / Discovered-not-indexed / Page with redirect / etc.). | Scaffolded — same pattern. |
| `recovery_metrics` | Derive weekly pre-vs-post migration summary: recovery ratio, anchor blogpost clicks, trend alerts. | Live (zero-filled until GSC lands). |

## Architecture

- Plain Python, `uv` + `pyproject.toml`.
- SQLAlchemy 2.x + Alembic. All tables in the `seo_pipeline` schema — migrations cannot touch the main eraluma app's tables.
- Every job writes a row to `run_log` on start and updates status/`rows_written`/error on finish. Errors are never silently swallowed.
- Alerts (`critical` / `warning` / `info`) are written to the `alerts` table. The dashboard surfaces unresolved alerts prominently.
- HTTP probes use `httpx` with HTTP/2 and Googlebot UA. Sitemap crawl runs 5 concurrent at 1 req/sec per host.

## Setup (local)

```bash
cd seo-pipeline
uv sync --extra dev
cp .env.example .env
# edit .env: DATABASE_URL + GSC_SERVICE_ACCOUNT_JSON_PATH
uv run alembic upgrade head
```

## CLI

```bash
uv run python -m seo_pipeline.run run redirect_health
uv run python -m seo_pipeline.run run sitemap_crawl
uv run python -m seo_pipeline.run run recovery_metrics
uv run python -m seo_pipeline.run run all
```

Pass `-v` before the subcommand for debug logging.

## Environment variables

| Var | Purpose |
| --- | --- |
| `DATABASE_URL` | Postgres DSN. Shared with eraluma; this pipeline writes only to the `seo_pipeline` schema. |
| `GSC_SERVICE_ACCOUNT_JSON_PATH` | Path to a Google service account JSON key with access to both GSC properties (`sc-domain:capetowndata.com` and `sc-domain:es-capetown.com`). Kept out of git. |
| `SITEMAP_CONCURRENCY` | Optional. Default 5. |
| `SITEMAP_REQUESTS_PER_SECOND` | Optional. Default 1.0. |

## Dashboard

The `src/seo_pipeline/api/` package is a Django app. To mount it in the eraluma project:

```python
# eraluma/settings.py
INSTALLED_APPS = [
    ...,
    "seo_pipeline.api.apps.SeoPipelineDashboardConfig",
]

# eraluma/urls.py
urlpatterns = [
    ...,
    path("seo/", include("seo_pipeline.api.urls")),
]
```

All views are `@staff_member_required`. Visit `/seo/dashboard/` once logged in as staff.

## Tests

```bash
uv run pytest
```

No live network calls — all HTTP is mocked via `httpx.MockTransport`. Run locally before committing.

## CI

`.github/workflows/cron.yml` runs Mon + Thu 07:00 UTC plus on-demand via `workflow_dispatch`. On failure, it opens a GitHub issue labelled `seo-pipeline, cron-failure`.

Required secrets (set once after pushing to a remote):

- `DATABASE_URL`
- `GSC_SERVICE_ACCOUNT_JSON` — the service account JSON content itself. The workflow writes it to a tempfile at runtime and wipes it on exit.

## Next: push to GitHub

This repo is local-only. To activate the cron:

```bash
gh repo create seo-pipeline --private --source=. --remote=origin
git push -u origin main
# then in the repo settings → Secrets and variables → Actions, add
# DATABASE_URL and GSC_SERVICE_ACCOUNT_JSON.
```

## Constraints this pipeline respects

- Never touches the `eraluma` repo or its tables.
- Never makes real GSC API calls during tests.
- Never stress-tests the origin — 1 req/sec, monitoring only.
- Never modifies Cloudflare configuration. The `redirect_health` job only reads; if it detects the SBFM pattern returning, it raises a critical alert and leaves the fix to a human.
