"""Tests for the pure-function helpers in src/sync_sheets.py.

The actual Sheets-API path is not tested (would require live credentials);
these cover only the local data shaping that runs before the API call.
"""
from __future__ import annotations


def test_cell_passes_through_simple_types():
    from src.sync_sheets import _cell
    assert _cell(None) == ""
    assert _cell(1) == 1
    assert _cell(1.5) == 1.5
    assert _cell("ok") == "ok"
    assert _cell(True) is True


def test_records_to_rows_emits_header_then_data():
    from src.sync_sheets import _records_to_rows
    matrix = _records_to_rows([
        {"a": 1, "b": "x"},
        {"a": 2, "b": "y"},
    ])
    assert matrix[0] == ["a", "b"]
    assert matrix[1] == [1, "x"]
    assert matrix[2] == [2, "y"]


def test_records_to_rows_unions_keys_across_rows():
    """Records with different key sets must align to the union of keys."""
    from src.sync_sheets import _records_to_rows
    matrix = _records_to_rows([
        {"a": 1, "b": "x"},
        {"a": 2, "c": "z"},
    ])
    assert matrix[0] == ["a", "b", "c"]
    assert matrix[1] == [1, "x", ""]
    assert matrix[2] == [2, "", "z"]


def test_records_to_rows_flattens_nested_brief():
    from src.sync_sheets import _records_to_rows
    matrix = _records_to_rows([
        {"cluster_id": 1, "brief": {"title": "T", "h2_outline": ["a", "b"]}},
    ])
    assert matrix[0] == ["cluster_id", "brief_title", "brief_h2_outline"]
    assert matrix[1] == [1, "T", "a | b"]
