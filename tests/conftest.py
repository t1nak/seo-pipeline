"""Pytest fixtures.

Nothing fancy — we mock all HTTP at the call site via httpx.MockTransport and
avoid touching the database in unit tests. Integration tests that need the DB
should be gated behind a marker we don't run in CI.
"""
