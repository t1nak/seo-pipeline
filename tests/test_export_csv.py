"""Tests for the CSV-flattening helpers in src/export.py."""
from __future__ import annotations


def test_csv_value_handles_empty_and_none():
    from src.export import _csv_value
    assert _csv_value(None) == ""
    assert _csv_value([]) == ""
    assert _csv_value("") == ""


def test_csv_value_joins_string_lists_with_pipe():
    from src.export import _csv_value
    assert _csv_value(["a", "b", "c"]) == "a | b | c"


def test_csv_value_formats_url_dicts():
    from src.export import _csv_value
    out = _csv_value([{"url": "https://a", "note": "n1"}])
    assert out == "https://a — n1"


def test_csv_value_converts_bool_to_string():
    from src.export import _csv_value
    assert _csv_value(True) == "true"
    assert _csv_value(False) == "false"


def test_flatten_for_csv_prefixes_nested_dict():
    from src.export import _flatten_for_csv
    record = {
        "cluster_id": 1,
        "brief": {
            "title": "x",
            "h2_outline": ["a", "b"],
        },
    }
    out = _flatten_for_csv(record)
    assert out["cluster_id"] == 1
    assert out["brief_title"] == "x"
    assert out["brief_h2_outline"] == "a | b"
