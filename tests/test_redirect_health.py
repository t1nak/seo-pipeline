"""Tests for redirect chain parsing and verdict classification."""

from __future__ import annotations

import httpx
import pytest

from seo_pipeline.jobs import redirect_health as rh
from seo_pipeline.jobs.redirect_health import Hop, ProbeResult, classify, probe_once


def _result(chain: list[tuple[int, str | None, bool]]) -> ProbeResult:
    r = ProbeResult(old_url="https://es-capetown.com/test/")
    r.chain = [
        Hop(url="https://es-capetown.com/test/", status=s, location=loc, cf_mitigated=cf)
        for s, loc, cf in chain
    ]
    if r.chain:
        last = r.chain[-1]
        r.final_status = last.status
        r.final_url = last.url
        r.cf_mitigated = any(h.cf_mitigated for h in r.chain)
    return r


def test_classify_clean_single_hop():
    r = _result([
        (301, "https://capetowndata.com/test/", False),
        (200, None, False),
    ])
    assert classify(r) == "CLEAN"


def test_classify_clean_two_hops():
    r = _result([
        (301, "https://capetowndata.com/en/products/safety/", False),
        (301, "https://capetowndata.com/en/safety/", False),
        (200, None, False),
    ])
    assert classify(r) == "CLEAN"


def test_classify_chain_more_than_two_redirects():
    r = _result([
        (301, "https://a", False),
        (301, "https://b", False),
        (301, "https://c", False),
        (200, None, False),
    ])
    assert classify(r) == "CHAIN"


def test_classify_broken_404():
    r = _result([
        (301, "https://capetowndata.com/missing/", False),
        (404, None, False),
    ])
    assert classify(r) == "BROKEN_404"


def test_classify_broken_5xx():
    r = _result([
        (301, "https://capetowndata.com/boom/", False),
        (502, None, False),
    ])
    assert classify(r) == "BROKEN_5XX"


def test_classify_blocked_cf_mitigated():
    r = _result([(403, None, True)])
    assert classify(r) == "BLOCKED"


def test_classify_no_redirect():
    r = _result([(200, None, False)])
    assert classify(r) == "NO_REDIRECT"


def test_classify_empty_chain_is_other():
    r = ProbeResult(old_url="https://example.com/")
    assert classify(r) == "OTHER"


# ---------------------------------------------------------------------------
# probe_once against a mocked transport
# ---------------------------------------------------------------------------


def _mock_transport(responses: dict[str, httpx.Response]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url in responses:
            return responses[url]
        return httpx.Response(404, text="not mapped")

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_probe_once_follows_301_to_200():
    old = "https://es-capetown.com/en/"
    new = "https://capetowndata.com/en/"
    transport = _mock_transport({
        old: httpx.Response(301, headers={"location": new}),
        new: httpx.Response(200, text="<html>ok</html>"),
    })
    async with httpx.AsyncClient(transport=transport) as client:
        result = await probe_once(client, old)

    assert result.verdict == "CLEAN"
    assert result.final_status == 200
    assert result.final_url == new
    assert result.hop_count == 2
    assert result.cf_mitigated is False


@pytest.mark.asyncio
async def test_probe_once_detects_cf_challenge():
    """The bellwether test: Cloudflare Super Bot Fight Mode returns 403 with
    cf-mitigated: challenge. This is exactly the pattern that broke the
    migration for two months."""
    old = "https://es-capetown.com/en/"
    transport = _mock_transport({
        old: httpx.Response(
            403,
            headers={"cf-mitigated": "challenge"},
            text="<html>challenge</html>",
        ),
    })
    async with httpx.AsyncClient(transport=transport) as client:
        result = await probe_once(client, old)

    assert result.verdict == "BLOCKED"
    assert result.cf_mitigated is True
    assert result.final_status == 403


@pytest.mark.asyncio
async def test_probe_once_two_hop_redirect():
    """Simulates the /products/safety/ → /safety/ flow: two 301s → 200."""
    a = "https://es-capetown.com/en/products/safety/"
    b = "https://capetowndata.com/en/products/safety/"
    c = "https://capetowndata.com/en/safety/"
    transport = _mock_transport({
        a: httpx.Response(301, headers={"location": b}),
        b: httpx.Response(301, headers={"location": c}),
        c: httpx.Response(200, text="<html>safety</html>"),
    })
    async with httpx.AsyncClient(transport=transport) as client:
        result = await probe_once(client, a)

    assert result.verdict == "CLEAN"
    assert result.hop_count == 3
    assert result.final_url == c


@pytest.mark.asyncio
async def test_probe_once_chain_too_long():
    """>2 redirect hops should flag as CHAIN even if it eventually resolves 200."""
    urls = [f"https://example.com/step{i}/" for i in range(5)]
    mapping: dict[str, httpx.Response] = {}
    for i, u in enumerate(urls[:-1]):
        mapping[u] = httpx.Response(301, headers={"location": urls[i + 1]})
    mapping[urls[-1]] = httpx.Response(200)

    transport = _mock_transport(mapping)
    async with httpx.AsyncClient(transport=transport) as client:
        result = await probe_once(client, urls[0])

    assert result.verdict == "CHAIN"


def test_probe_urls_includes_safety_paths_all_locales():
    urls = rh.probe_urls()
    for lang in ("de", "en", "es", "fr", "it", "ja", "nl", "pt", "ru"):
        assert any(f"/{lang}/products/safety/" in u for u in urls), (
            f"safety path missing for locale {lang}"
        )


def test_probe_urls_no_duplicates():
    urls = rh.probe_urls()
    assert len(urls) == len(set(urls))
