"""Tests for the pure-function helpers in src/sync_airtable.py."""
from __future__ import annotations


def test_airtable_value_joins_string_lists():
    from src.sync_airtable import _airtable_value
    assert _airtable_value(["a", "b", "c"]) == "a | b | c"
    assert _airtable_value([]) == ""


def test_airtable_value_serializes_url_dicts():
    from src.sync_airtable import _airtable_value
    out = _airtable_value([
        {"url": "https://a.example", "note": "good"},
        {"url": "https://b.example", "note": "ok"},
    ])
    assert out == "https://a.example — good | https://b.example — ok"


def test_to_airtable_fields_drops_empty_and_casts_bool_strings():
    from src.sync_airtable import _to_airtable_fields
    record = {
        "cluster_id": 1,
        "is_noise": False,
        "empty_str": "",
        "none_val": None,
        "label_de": "Test",
    }
    out = _to_airtable_fields(record)
    assert out["cluster_id"] == 1
    assert out["is_noise"] is False
    assert out["label_de"] == "Test"
    assert "empty_str" not in out
    assert "none_val" not in out


def test_to_airtable_fields_flattens_nested_brief():
    from src.sync_airtable import _to_airtable_fields
    record = {
        "cluster_id": 1,
        "brief": {
            "title": "Test Title",
            "h2_outline": ["a", "b"],
            "recommended_word_count": 2500,
        },
    }
    out = _to_airtable_fields(record)
    assert out["brief_title"] == "Test Title"
    assert out["brief_h2_outline"] == "a | b"
    assert out["brief_recommended_word_count"] == 2500
