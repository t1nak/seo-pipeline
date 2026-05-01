"""End-to-end orchestrator for the SEO keyword pipeline.

Six steps in order:

    1. discover    blog -> seed keywords -> data/keywords.csv
    2. enrich      add SV / KD / CPC / priority to data/keywords.csv
    3. cluster     embed -> UMAP -> HDBSCAN -> labels -> profiles -> charts -> map
    4. brief       per-cluster content brief via Claude API -> output/briefings/
    5. report      consolidated HTML report -> output/reporting/index.html
    6. export      filterbares JSON-Reporting -> output/reporting/{clusters,keywords,report}.json

CLI:
    python pipeline.py                              run all 6 steps
    python pipeline.py --step cluster               run one step
    python pipeline.py --step brief,report,export   run a subset
    python pipeline.py --dry-run                    skip LLM call in brief
    python pipeline.py --brief-provider max         brief via Max subscription
    python pipeline.py --brief-provider api --brief-model claude-opus-4-7
    python pipeline.py --brief-provider openai --brief-model gpt-5

Each step can also be invoked directly via its own module CLI for finer
control. See src/cluster.py and src/brief.py for sub-CLIs.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src import brief, cluster, discover, enrich, export, report  # noqa: E402
from src.config import settings  # noqa: E402
from src.logging_config import setup_logging  # noqa: E402

logger = logging.getLogger(__name__)

ALL_STEPS = ("discover", "enrich", "cluster", "brief", "report", "export")


def step_discover(args: argparse.Namespace) -> None:
    source = args.source or settings.discover_source
    if source == "manual":
        discover.discover_manual(max_keywords=settings.discover_max_keywords)
    else:
        discover.discover_live()


def step_enrich(args: argparse.Namespace) -> None:
    provider = args.provider or settings.enrich_provider
    enrich.run(provider=provider,
               in_csv=ROOT / "data" / "keywords.csv",
               out_csv=ROOT / "data" / "keywords.csv")


def step_cluster(args: argparse.Namespace) -> None:
    for s in cluster.DEFAULT_SEQUENCE:
        logger.info(f"\n=== cluster.{s} ===")
        cluster.STEPS[s]()


def step_brief(args: argparse.Namespace) -> None:
    brief.run(provider_name=args.brief_provider or settings.brief_provider,
              model=args.brief_model or settings.brief_model,
              dry_run=args.dry_run)


def step_report(args: argparse.Namespace) -> None:
    report.run()


def step_export(args: argparse.Namespace) -> None:
    export.run()


RUNNERS = {
    "discover": step_discover,
    "enrich": step_enrich,
    "cluster": step_cluster,
    "brief": step_brief,
    "report": step_report,
    "export": step_export,
}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--step", default="all",
                   help="comma-separated steps from: " + ", ".join(ALL_STEPS) + " (or 'all')")
    p.add_argument("--source", choices=["manual", "live"], default=None,
                   help=f"discover step source. Default from settings: {settings.discover_source}.")
    p.add_argument("--provider", choices=["estimate", "dataforseo"], default=None,
                   help=f"enrich step provider. Default from settings: {settings.enrich_provider}.")
    p.add_argument("--brief-provider", choices=["api", "openai", "max"], default=None,
                   help="brief step LLM provider. "
                        "api: ANTHROPIC_API_KEY. "
                        "openai: OPENAI_API_KEY. "
                        "max: local Claude Code session via claude-agent-sdk. "
                        f"Default from settings: {settings.brief_provider}.")
    p.add_argument("--brief-model", default=None,
                   help="brief step model id, valid with --brief-provider api or openai. "
                        "Defaults: api=claude-sonnet-4-6, openai=gpt-5. "
                        f"Settings default: {settings.brief_model or 'provider default'}.")
    p.add_argument("--dry-run", action="store_true",
                   help="brief step: write stubs instead of calling the LLM")
    p.add_argument("--log-level", default=None,
                   help=f"DEBUG, INFO, WARNING, ERROR. Default from settings: {settings.log_level}.")
    args = p.parse_args()

    setup_logging(level=args.log_level)

    requested = (ALL_STEPS if args.step == "all"
                 else tuple(s.strip() for s in args.step.split(",")))
    unknown = [s for s in requested if s not in RUNNERS]
    if unknown:
        raise SystemExit(f"unknown step(s): {unknown}. valid: {list(RUNNERS)}")

    for name in requested:
        logger.info(f"\n========== {name.upper()} ==========")
        RUNNERS[name](args)
    logger.info("\n========== DONE ==========")


if __name__ == "__main__":
    main()
