"""Smoke tests for the pipeline.

These don't run the heavy ML steps (embeddings, UMAP, HDBSCAN). They
exercise the orchestration paths that are easy to break: the report
step (writes HTML from existing CSVs), the brief --dry-run path (writes
stubs without an LLM call), and the briefs_html dashboard renderer.

If `cluster_profiles.csv` and `keywords_labeled.csv` exist (they do
after a normal pipeline run), these tests run in well under a second.
If they do not exist, the tests are skipped, not failed.
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PROFILES_CSV = ROOT / "output" / "clustering" / "cluster_profiles.csv"
LABELED_CSV = ROOT / "output" / "clustering" / "keywords_labeled.csv"


pytestmark = pytest.mark.skipif(
    not (PROFILES_CSV.exists() and LABELED_CSV.exists()),
    reason="cluster artefacts missing; run `python -m src.cluster` first",
)


def test_report_writes_html(tmp_path, monkeypatch):
    """report.run() should produce a non-empty index.html."""
    from src import report
    out = ROOT / "output" / "reporting" / "index.html"
    before = out.read_bytes() if out.exists() else b""
    report.run()
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "<html" in content.lower()
    assert "Cluster" in content
    assert "Keywords" in content


def test_briefs_html_writes_dashboard():
    """briefs_html should render a card dashboard with one card per cluster."""
    from src import briefs_html
    briefs_html.run()
    out = ROOT / "output" / "briefings" / "index.html"
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "<html" in text.lower()
    assert "Cluster Briefs" in text
    assert "Glossar" in text  # the modal trigger button


def test_brief_dry_run_does_not_overwrite_real_briefs(tmp_path, monkeypatch):
    """The safety net in brief.run(dry_run=True) skips files that look like
    full structured briefs."""
    from src import brief

    # Sandbox: temporarily redirect BRIEFINGS into tmp_path
    sandbox = tmp_path / "briefings"
    sandbox.mkdir()
    real = sandbox / "cluster_01.md"
    real.write_text(
        "# Echter Titel\n\n"
        "**Hauptkeyword:** factoring buchen\n\n"
        "## Outline\n- H1: ...\n",
        encoding="utf-8",
    )
    real_before = real.read_text()

    monkeypatch.setattr(brief, "BRIEFINGS", sandbox)
    brief.run(dry_run=True)

    assert real.read_text() == real_before, "real brief was overwritten"
