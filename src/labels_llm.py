"""Generate cluster labels dynamically via LLM.

Replaces hand-curated `data/cluster_labels.yaml` with labels derived from
the actual cluster content (top keywords + top terms). Runs as a separate
pipeline step between `cluster` and `brief` so any number of clusters
(10, 12, 13, ...) gets meaningful German + English labels without manual
intervention.

Output:
    output/clustering/cluster_labels.json
        {"-1": {"de": "...", "en": "..."}, "0": {...}, ...}

Side effect: updates `hdb_label` / `hdb_label_de` columns in
keywords_labeled.csv and `label_en` / `label_de` in cluster_profiles.csv
so the dashboard, charts, and cluster map pick up the new labels.

Single batch call (one Anthropic request for all clusters) keeps cost
flat at ~1 cent regardless of cluster count.

CLI:
    python -m src.labels_llm                     api + ANTHROPIC_API_KEY, haiku
    python -m src.labels_llm --model claude-sonnet-4-6
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd

from src.logging_config import setup_logging
from src.retry import with_retry

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
CLUSTERING = OUT / "clustering"
PROFILES_CSV = CLUSTERING / "cluster_profiles.csv"
LABELED_CSV = CLUSTERING / "keywords_labeled.csv"
LABELS_JSON = CLUSTERING / "cluster_labels.json"

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 2000

SYSTEM_PROMPT = """Du bist Senior Content Strategist für den deutschen B2B SaaS Markt.
Spezialgebiet: Personaldienstleistung, Zeitarbeit, Recruiting Software, Compliance.

Du bekommst Cluster aus einer SEO-Keyword-Pipeline. Jeder Cluster ist eine Gruppe semantisch ähnlicher Keywords. Erzeuge für jeden Cluster ein präzises Label in zwei Sprachen:

- Deutsch: 3 bis 5 Wörter, kein "Cluster", keine Anführungszeichen, kein Punkt am Ende.
- Englisch: 3 bis 5 Wörter, gleiche Regeln.

Das Label muss den thematischen Kern erfassen. Vermeide generische Begriffe ("HR Themen", "Verschiedenes"). Wenn ein Cluster sehr breit ist, kennzeichne das mit "Sammelthemen" oder "Catch-all" im Label.

Antwort: NUR ein JSON-Array, kein Vorwort, keine Markdown-Codefences. Schema:
[{"cluster_id": 0, "label_de": "...", "label_en": "..."}, ...]"""


def _build_user_prompt(profiles: pd.DataFrame) -> str:
    real = profiles[profiles["cluster_id"] != -1].copy()
    blocks = []
    for _, r in real.iterrows():
        blocks.append(
            f"[CLUSTER {int(r['cluster_id'])}]\n"
            f"n_keywords: {int(r['n_keywords'])}\n"
            f"top_5_keywords_by_search_volume: {r['top_5_kw_by_sv']}\n"
            f"top_3_keywords_by_priority: {r['top_3_kw_by_priority']}\n"
            f"frequent_terms: {r['top_terms']}"
        )
    return "Erzeuge für die folgenden Cluster Labels:\n\n" + "\n\n".join(blocks)


@with_retry()
def _call_llm(system: str, user: str, model: str) -> str:
    try:
        from anthropic import Anthropic
    except ImportError:
        sys.exit("anthropic SDK not installed. `pip install anthropic`.")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ANTHROPIC_API_KEY not set.")
    client = Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text


def _parse_labels(text: str) -> dict[int, dict[str, str]]:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    parsed = json.loads(text)
    out: dict[int, dict[str, str]] = {}
    for entry in parsed:
        cid = int(entry["cluster_id"])
        out[cid] = {"de": entry["label_de"].strip(), "en": entry["label_en"].strip()}
    return out


def run(model: str = DEFAULT_MODEL) -> None:
    if not PROFILES_CSV.exists():
        sys.exit(f"missing {PROFILES_CSV}. Run cluster step first.")
    profiles = pd.read_csv(PROFILES_CSV)
    labeled = pd.read_csv(LABELED_CSV)

    logger.info("calling %s for labels of %d clusters",
                model, int((profiles["cluster_id"] != -1).sum()))
    user = _build_user_prompt(profiles)
    raw = _call_llm(SYSTEM_PROMPT, user, model)
    labels = _parse_labels(raw)

    labels[-1] = {"de": "Rauschen / Ausreißer", "en": "Noise / outliers"}

    out_json = {str(cid): v for cid, v in labels.items()}
    LABELS_JSON.write_text(json.dumps(out_json, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("wrote %s", LABELS_JSON.relative_to(ROOT))

    profiles["label_en"] = profiles["cluster_id"].apply(
        lambda c: labels.get(int(c), {"en": f"Cluster {int(c) + 1}"})["en"])
    profiles["label_de"] = profiles["cluster_id"].apply(
        lambda c: labels.get(int(c), {"de": f"Cluster {int(c) + 1}"})["de"])
    profiles.to_csv(PROFILES_CSV, index=False)

    def _label(cid: int, lang: str) -> str:
        if int(cid) == -1:
            return ""
        return labels.get(int(cid), {lang: f"Cluster {int(cid) + 1}"})[lang]

    labeled["hdb_label"] = labeled["hdb"].apply(lambda c: _label(c, "en"))
    labeled["hdb_label_de"] = labeled["hdb"].apply(lambda c: _label(c, "de"))
    labeled.to_csv(LABELED_CSV, index=False)
    logger.info("updated label columns in cluster_profiles.csv and keywords_labeled.csv")


def main() -> None:
    setup_logging()
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--model", default=DEFAULT_MODEL,
                   help=f"Anthropic model id. Default: {DEFAULT_MODEL}")
    args = p.parse_args()
    run(model=args.model)


if __name__ == "__main__":
    main()
