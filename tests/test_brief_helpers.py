"""Tests for the pure-function helpers in src/brief.py."""
from __future__ import annotations

from pathlib import Path


# These imports are at module scope, not inside functions, because brief.py
# is now safe to import without side effects (it does not call setup_logging
# or open any client at import time).


def test_strip_preamble_drops_narration():
    """Agent-style providers prepend 'Ich recherchiere ...' before the H1.
    The brief module strips anything before the first '# ' line.
    """
    from src.brief import _strip_preamble

    raw = (
        "Ich recherchiere die zvoove Produktnamen jetzt...\n\n"
        "Mit den Top Keywords vor mir, schreibe ich:\n\n"
        "# Marke zvoove: Module und Erfahrungen\n\n"
        "**Hauptkeyword:** zvoove referenzen\n"
    )
    cleaned = _strip_preamble(raw)
    assert cleaned.startswith("# Marke zvoove")
    assert "Ich recherchiere" not in cleaned


def test_strip_preamble_passthrough_when_already_clean():
    from src.brief import _strip_preamble

    clean = "# Title\n\nbody"
    assert _strip_preamble(clean) == "# Title\n\nbody"


def test_stub_brief_contains_top_keywords():
    from src.brief import _stub_brief

    out = _stub_brief(
        cluster_id=4,
        label_de="Marke: zvoove Produktnamen",
        top_kw=["zvoove referenzen", "zvoove dms", "zvoove cockpit",
                "zvoove payroll", "zvoove cashlink", "zvoove recruit"],
    )
    assert "Cluster 5" in out  # display id is cluster_id + 1
    assert "Status:** Stub" in out
    assert "zvoove referenzen" in out
    assert "Marke: zvoove Produktnamen" in out
    # Stubs only show top 5 keywords, not all of them
    assert "zvoove recruit" not in out


def test_looks_like_real_brief_distinguishes_real_from_stub(tmp_path):
    """The safety net: dry-run must skip files that already contain a
    structured (real) brief, but happily overwrite stubs.
    """
    from src.brief import _looks_like_real_brief

    real = tmp_path / "real.md"
    real.write_text(
        "# Echter Titel\n\n"
        "**Hauptkeyword:** factoring buchen\n"
        "**Nebenkeywords:** factoring erlaubnis\n\n"
        "## Zielgruppe\nKaufmännische Leiter ...\n\n"
        "## Outline\n- H1: ...\n",
        encoding="utf-8",
    )
    assert _looks_like_real_brief(real) is True

    stub = tmp_path / "stub.md"
    stub.write_text(
        "# Cluster 1: Factoring-Grundlagen\n\n"
        "**Status:** Stub (dry run mode, kein LLM Aufruf).\n",
        encoding="utf-8",
    )
    assert _looks_like_real_brief(stub) is False

    missing = tmp_path / "does_not_exist.md"
    assert _looks_like_real_brief(missing) is False
