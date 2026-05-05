"""Tests for the pure-function helpers in src/export.py."""
from __future__ import annotations


def test_split_kw_list_handles_empty_and_nan():
    from src.export import _split_kw_list
    assert _split_kw_list("") == []
    assert _split_kw_list(None) == []
    assert _split_kw_list("a; b ; ;c") == ["a", "b", "c"]


def test_split_secondary_splits_on_comma():
    from src.export import _split_secondary
    assert _split_secondary("a, b ,c") == ["a", "b", "c"]
    assert _split_secondary("") == []


def test_intent_from_pct_thresholds():
    from src.export import _intent_from_pct
    assert _intent_from_pct(80) == "commercial"
    assert _intent_from_pct(70) == "commercial"
    assert _intent_from_pct(50) == "mixed"
    assert _intent_from_pct(20) == "informational"
    assert _intent_from_pct(0) == "informational"


def test_parse_word_count_extracts_first_number():
    from src.export import _parse_word_count
    assert _parse_word_count("2500") == 2500
    assert _parse_word_count("2500 Wörter") == 2500
    assert _parse_word_count("ca. 2800 bis 3200") == 2800
    assert _parse_word_count("") is None
    assert _parse_word_count("kein Wert") is None


def test_parse_benchmark_urls_pulls_url_and_note():
    from src.export import _parse_benchmark_urls
    md = (
        "## Benchmark URLs\n\n"
        "1. https://a.example/x — solide Grundlagen\n"
        "2. https://b.example/y - Praxisbezug stark\n"
        "3. nope keine URL hier\n"
    )
    out = _parse_benchmark_urls(md)
    assert len(out) == 2
    assert out[0] == {"url": "https://a.example/x", "note": "solide Grundlagen"}
    assert out[1] == {"url": "https://b.example/y", "note": "Praxisbezug stark"}
