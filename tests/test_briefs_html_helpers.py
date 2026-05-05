"""Tests for the pure-function helpers in src/briefs_html.py."""
from __future__ import annotations

import math


def test_safe_label_returns_value_when_present():
    from src.briefs_html import _safe_label
    assert _safe_label("Factoring-Grundlagen", 1) == "Factoring-Grundlagen"


def test_safe_label_falls_back_for_nan():
    """pandas reads empty CSV cells as float NaN; the bare `value or fallback`
    pattern previously leaked NaN into htmllib.escape and crashed the report."""
    from src.briefs_html import _safe_label
    assert _safe_label(math.nan, 11) == "Cluster 11"


def test_safe_label_falls_back_for_empty_string():
    from src.briefs_html import _safe_label
    assert _safe_label("", 12) == "Cluster 12"
    assert _safe_label("   ", 12) == "Cluster 12"
