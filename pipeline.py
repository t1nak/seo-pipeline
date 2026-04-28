"""End-to-end orchestrator for the SEO keyword pipeline.

Five steps in order:

    1. discover    blog -> seed keywords -> data/keywords.csv
    2. enrich      add SV / KD / CPC / priority to data/keywords.csv
    3. cluster     embed -> UMAP -> HDBSCAN -> labels -> profiles -> charts -> map
    4. brief       per-cluster content brief via Claude API -> output/briefings/
    5. report      consolidated HTML report -> output/reporting/index.html

CLI:
    python pipeline.py                       run all 5 steps
    python pipeline.py --step cluster        run one step
    python pipeline.py --step brief,report   run a subset
    python pipeline.py --dry-run             skip API calls (for brief)

Each step can also be invoked directly via its own module CLI for finer
control. See src/cluster.py for the cluster sub-step CLI.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src import brief, cluster, discover, enrich, report  # noqa: E402

ALL_STEPS = ("discover", "enrich", "cluster", "brief", "report")


def step_discover(args: argparse.Namespace) -> None:
    if args.source == "manual":
        discover.discover_manual()
    else:
        discover.discover_live()


def step_enrich(args: argparse.Namespace) -> None:
    enrich.run(provider=args.provider,
               in_csv=ROOT / "data" / "keywords.csv",
               out_csv=ROOT / "data" / "keywords.csv")


def step_cluster(args: argparse.Namespace) -> None:
    for s in cluster.DEFAULT_SEQUENCE:
        print(f"\n=== cluster.{s} ===")
        cluster.STEPS[s]()


def step_brief(args: argparse.Namespace) -> None:
    brief.run(dry_run=args.dry_run)


def step_report(args: argparse.Namespace) -> None:
    report.run()


RUNNERS = {
    "discover": step_discover,
    "enrich": step_enrich,
    "cluster": step_cluster,
    "brief": step_brief,
    "report": step_report,
}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--step", default="all",
                   help="comma-separated steps from: " + ", ".join(ALL_STEPS) + " (or 'all')")
    p.add_argument("--source", choices=["manual", "live"], default="manual",
                   help="discover step source")
    p.add_argument("--provider", choices=["estimate", "dataforseo"], default="estimate",
                   help="enrich step provider")
    p.add_argument("--dry-run", action="store_true",
                   help="brief step: write stubs instead of calling Claude API")
    args = p.parse_args()

    requested = (ALL_STEPS if args.step == "all"
                 else tuple(s.strip() for s in args.step.split(",")))
    unknown = [s for s in requested if s not in RUNNERS]
    if unknown:
        raise SystemExit(f"unknown step(s): {unknown}. valid: {list(RUNNERS)}")

    for name in requested:
        print(f"\n========== {name.upper()} ==========")
        RUNNERS[name](args)
    print("\n========== DONE ==========")


if __name__ == "__main__":
    main()
