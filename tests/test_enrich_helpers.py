"""Tests for the deterministic heuristic in src/enrich.py.

The heuristic seeds a per-keyword PRNG from the SHA256 hash of the keyword.
That gives us the property `estimate(row) == estimate(row)` across runs,
which the rest of the pipeline relies on for reproducibility.
"""
from __future__ import annotations


def test_estimate_is_deterministic():
    """Same input must yield the exact same output, every time."""
    from src.enrich import estimate

    row = {"keyword": "zvoove cockpit",
           "type": "head", "estimated_intent": "commercial"}
    a = estimate(row)
    b = estimate(row)
    assert a == b


def test_estimate_returns_expected_keys():
    from src.enrich import estimate

    row = {"keyword": "factoring buchen",
           "type": "body", "estimated_intent": "informational"}
    result = estimate(row)
    expected = {"search_volume", "kd", "cpc_eur",
                "serp_features", "priority_score", "data_source"}
    assert set(result.keys()) == expected
    assert result["data_source"] == "estimated"


def test_estimate_volume_in_range_for_intent_type():
    """Heuristic ranges per (intent, type). A head/commercial keyword
    should get higher SV than a longtail/informational one (mostly).
    Exact values depend on the hash seed; this test checks structure
    (numeric, in-range) rather than specific numbers.
    """
    from src.enrich import estimate, VOL_RANGE

    head_row = {"keyword": "zeitarbeitssoftware",
                "type": "head", "estimated_intent": "commercial"}
    head = estimate(head_row)
    vlo, vhi = VOL_RANGE["head"]
    assert vlo <= head["search_volume"] <= vhi


def test_estimate_kd_clamped_to_1_95():
    """KD must always land in [1, 95] regardless of the type bonus."""
    from src.enrich import estimate

    for kw in ["abc", "def", "ghi", "ein paar tests"]:
        for typ in ["head", "body", "longtail"]:
            for intent in ["commercial", "informational",
                           "transactional", "navigational"]:
                r = estimate({"keyword": kw, "type": typ,
                              "estimated_intent": intent})
                assert 1 <= r["kd"] <= 95, f"kd out of range for {kw}/{typ}/{intent}"


def test_priority_score_is_volume_over_kd():
    """priority_score = round(volume / max(kd, 5), 1). Defensive against KD=0."""
    from src.enrich import estimate

    r = estimate({"keyword": "abc", "type": "body",
                  "estimated_intent": "commercial"})
    expected = round(r["search_volume"] / max(r["kd"], 5), 1)
    assert r["priority_score"] == expected
