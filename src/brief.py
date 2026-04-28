"""Brief step of the SEO keyword pipeline.

For each HDBSCAN cluster, generates a German content brief and writes it
as Markdown to `output/briefings/cluster_{nn}.md`.

The brief structure follows what an editor would expect for a B2B SaaS blog:

  * Arbeitstitel (working title)
  * Zielgruppe (audience persona)
  * Schmerzpunkt (pain point) and Ziel (goal of the article)
  * Suchintention (search intent classification)
  * H1 to H3 outline
  * Empfohlene Wortanzahl (recommended word count)
  * Drei Wettbewerbs-URLs als Benchmarks (three benchmark URLs to study)
  * Call to action

Real Claude API in default mode. `--dry-run` writes a stub per cluster
(useful for offline iteration on the rest of the pipeline).

Authentication: this module uses the `anthropic` SDK with an API key
(env var `ANTHROPIC_API_KEY`). For solo developers already paying for
a Claude Max or Pro subscription, the alternative `claude-agent-sdk`
wraps the local Claude Code CLI session and avoids the separate API
billing. We chose the API key path as the documented default because
it is reproducible in CI and deployable to serverless. Trade-off and
recommendation are in docs/decisions.md (ADR-11).

Prompt caching: the system prompt is stable across all clusters, so it
is sent as a cached block. This cuts per-call cost on repeated runs by
roughly 90% on the cached portion.

CLI:
    python -m src.brief                     real Claude API (needs ANTHROPIC_API_KEY)
    python -m src.brief --dry-run            stub mode, no API calls
    python -m src.brief --cluster 5          regenerate just one cluster
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
BRIEFINGS = OUT / "briefings"
PROFILES_CSV = OUT / "clustering" / "cluster_profiles.csv"
LABELED_CSV = OUT / "clustering" / "keywords_labeled.csv"

MODEL_ID = "claude-sonnet-4-6"
MAX_TOKENS = 4096

SYSTEM_PROMPT = """Du bist Senior Content Strategist für den deutschen B2B SaaS Markt.
Spezialgebiet: Personaldienstleistung, Zeitarbeit, Recruiting Software, Compliance.

Deine Aufgabe: pro Keyword Cluster einen Content Brief für einen Blog Artikel erstellen,
der für Google rankt und gleichzeitig echte Kaufinteressenten anspricht.

Format des Briefs (immer Markdown, immer Deutsch, immer in dieser Reihenfolge):

# {Arbeitstitel}

**Hauptkeyword:** {hauptkeyword}
**Nebenkeywords:** {3 bis 7 nebenkeywords}
**Suchintention:** {commercial / informational / mixed}, {1 Satz Begründung}
**Empfohlene Wortanzahl:** {1500 bis 3500}

## Zielgruppe

{1 Satz Persona, konkrete Rolle und Firmengröße}

## Schmerzpunkt

{2 bis 3 Sätze, was diese Person nachts wachhält}

## Ziel des Artikels

{1 Satz, was der Leser nach dem Lesen tun oder verstanden haben soll}

## Outline

- H1: {Titel}
- H2: {Section 1}
  - H3: ...
- H2: {Section 2}
  - H3: ...
{4 bis 7 H2 Abschnitte mit jeweils 1 bis 4 H3 Unterpunkten}

## Benchmark URLs

1. {URL eines direkten Wettbewerbers oder eines hoch rankenden Artikels} — {warum relevant}
2. ...
3. ...

## Call to Action

{1 konkrete Aktion, idealerweise mit Bezug zu zvoove Produkten}

Schreibe pragmatisch, nicht akademisch. Keine Floskeln. Keine KI Erkennungsmerkmale
wie Gedankenstriche. Nutze Komma, Doppelpunkt, oder neuen Satz."""


def _user_prompt(cluster_id: int, label_de: str, profile: dict, top_kw: list[str]) -> str:
    """Per-cluster prompt assembled from the cluster profile and the top keywords."""
    return (
        f"CLUSTER {cluster_id + 1}: {label_de}\n\n"
        f"Statistiken:\n"
        f"  Anzahl Keywords im Cluster: {profile['n_keywords']}\n"
        f"  Gesamt Suchvolumen pro Monat: {profile['total_sv']}\n"
        f"  Mittlere Keyword Difficulty: {profile['mean_kd']}\n"
        f"  Mittlerer CPC: {profile['mean_cpc']} EUR\n"
        f"  Anteil kommerzielle Keywords: {profile['pct_commercial']} Prozent\n\n"
        f"Top Keywords nach Suchvolumen:\n"
        + "\n".join(f"  - {kw}" for kw in top_kw)
        + "\n\nErstelle einen Content Brief für diesen Cluster nach dem oben definierten Format."
    )


def _stub_brief(cluster_id: int, label_de: str, top_kw: list[str]) -> str:
    """Used in --dry-run mode and as fallback when the API call fails."""
    return (
        f"# Cluster {cluster_id + 1}: {label_de}\n\n"
        f"**Status:** Stub (dry run mode, kein LLM Aufruf).\n\n"
        f"**Top Keywords:**\n"
        + "\n".join(f"- {kw}" for kw in top_kw[:5])
        + "\n\nFür einen vollständigen Brief mit `python -m src.brief --cluster "
        f"{cluster_id}` und gesetztem ANTHROPIC_API_KEY neu generieren.\n"
    )


def _generate_brief(client, cluster_id: int, label_de: str,
                    profile: dict, top_kw: list[str]) -> str:
    """One Claude API call. System prompt is cached across calls."""
    system_blocks = [{
        "type": "text",
        "text": SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral"},
    }]
    msg = client.messages.create(
        model=MODEL_ID,
        max_tokens=MAX_TOKENS,
        system=system_blocks,
        messages=[{"role": "user", "content": _user_prompt(cluster_id, label_de, profile, top_kw)}],
    )
    return msg.content[0].text


def run(dry_run: bool = False, cluster_filter: int | None = None) -> None:
    if not PROFILES_CSV.exists() or not LABELED_CSV.exists():
        sys.exit(f"missing inputs. Expected {PROFILES_CSV.relative_to(ROOT)} and "
                 f"{LABELED_CSV.relative_to(ROOT)}. Run `python -m src.cluster --step all` first.")

    BRIEFINGS.mkdir(parents=True, exist_ok=True)
    profiles = pd.read_csv(PROFILES_CSV)
    labeled = pd.read_csv(LABELED_CSV)

    client = None
    if not dry_run:
        try:
            from anthropic import Anthropic
        except ImportError:
            sys.exit("anthropic SDK not installed. `pip install anthropic` or use --dry-run.")
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            sys.exit("ANTHROPIC_API_KEY not set. Export it or use --dry-run.")
        client = Anthropic(api_key=api_key)

    n_ok = n_fail = n_skip = 0
    for _, row in profiles.iterrows():
        cid = int(row["cluster_id"])
        if cid == -1:
            continue  # skip noise cluster
        if cluster_filter is not None and cid != cluster_filter:
            continue

        label_de = row["label_de"]
        top_kw = labeled.loc[labeled["hdb"] == cid].sort_values(
            "search_volume", ascending=False).head(10)["keyword"].tolist()
        out_path = BRIEFINGS / f"cluster_{cid + 1:02d}.md"

        if dry_run:
            out_path.write_text(_stub_brief(cid, label_de, top_kw))
            print(f"[brief] (dry-run) {out_path.relative_to(ROOT)}")
            n_ok += 1
            continue

        try:
            text = _generate_brief(client, cid, label_de, row.to_dict(), top_kw)
            out_path.write_text(text)
            print(f"[brief] {out_path.relative_to(ROOT)} ({len(text)} chars)")
            n_ok += 1
        except Exception as exc:
            print(f"[brief] cluster {cid} FAILED: {exc}", file=sys.stderr)
            out_path.write_text(_stub_brief(cid, label_de, top_kw))
            n_fail += 1

    print(f"\n[brief] done. ok={n_ok} failed={n_fail} skipped={n_skip}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--dry-run", action="store_true", help="skip API calls, write stubs")
    p.add_argument("--cluster", type=int, default=None,
                   help="only generate this cluster id (0-based)")
    args = p.parse_args()
    run(dry_run=args.dry_run, cluster_filter=args.cluster)


if __name__ == "__main__":
    main()
