"""CLI entry point: `python -m seo_pipeline.run <job>`.

Jobs:
  all              run every job in order
  gsc_performance  pull last-28d GSC performance data
  gsc_indexation   snapshot per-domain coverage state counts
  sitemap_crawl    crawl capetowndata.com sitemap + probe URLs
  redirect_health  probe old-domain URLs for redirect regressions
  recovery_metrics derive weekly pre-vs-post migration summary

Each job manages its own run_log entry and never silently swallows errors.
"""

from __future__ import annotations

import logging
import sys
from typing import Callable

import click

from .jobs import (
    gsc_indexation,
    gsc_performance,
    recovery_metrics,
    redirect_health,
    sitemap_crawl,
)

JOBS: dict[str, Callable[[], None]] = {
    "gsc_performance": gsc_performance.run,
    "gsc_indexation": gsc_indexation.run,
    "sitemap_crawl": sitemap_crawl.run,
    "redirect_health": redirect_health.run,
    "recovery_metrics": recovery_metrics.run,
}

# Execution order for "all": gather raw data first, then derive.
ALL_ORDER = (
    "gsc_performance",
    "gsc_indexation",
    "sitemap_crawl",
    "redirect_health",
    "recovery_metrics",
)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging.")
def cli(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


@cli.command()
@click.argument("job", type=click.Choice(["all", *JOBS.keys()]))
def run(job: str) -> None:
    """Run a single job or all jobs."""
    if job == "all":
        failures: list[tuple[str, Exception]] = []
        for name in ALL_ORDER:
            click.echo(f"\n== {name} ==")
            try:
                JOBS[name]()
            except Exception as exc:
                failures.append((name, exc))
                click.echo(f"!! {name} FAILED: {exc}", err=True)
        if failures:
            sys.exit(1)
        return

    JOBS[job]()


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
