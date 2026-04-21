"""Tests for sitemap URL classification and probing."""

from __future__ import annotations

import httpx
import pytest

from seo_pipeline.jobs.sitemap_crawl import (
    classify_url,
    _fetch_sitemap_urls,
    _parse_html,
    _probe_one,
)


class TestClassifyUrl:
    def test_language_root(self):
        c = classify_url("https://capetowndata.com/en/")
        assert c.url_type == "language_root"
        assert c.locale == "en"
        assert c.blogpost_id is None

    def test_language_root_without_trailing_slash(self):
        c = classify_url("https://capetowndata.com/de")
        assert c.url_type == "language_root"
        assert c.locale == "de"

    def test_blogpost(self):
        c = classify_url("https://capetowndata.com/en/products/blogpost/140/")
        assert c.url_type == "blogpost"
        assert c.locale == "en"
        assert c.blogpost_id == 140

    def test_blogpost_all_locales(self):
        for lang in ("de", "en", "es", "fr", "it", "ja", "nl", "pt", "ru"):
            c = classify_url(f"https://capetowndata.com/{lang}/products/blogpost/42/")
            assert c.url_type == "blogpost"
            assert c.locale == lang
            assert c.blogpost_id == 42

    def test_safety_hub(self):
        c = classify_url("https://capetowndata.com/en/safety/")
        assert c.url_type == "safety_hub"
        assert c.locale == "en"

    def test_safety_subpage(self):
        c = classify_url(
            "https://capetowndata.com/en/safety/sea-point/"
        )
        assert c.url_type == "safety_subpage"
        assert c.locale == "en"

    def test_other_within_locale(self):
        c = classify_url("https://capetowndata.com/en/about/")
        assert c.url_type == "other"
        assert c.locale == "en"

    def test_other_no_locale(self):
        c = classify_url("https://capetowndata.com/robots.txt")
        assert c.url_type == "other"
        assert c.locale is None

    def test_invalid_locale_is_other(self):
        c = classify_url("https://capetowndata.com/xx/products/blogpost/140/")
        assert c.url_type == "other"

    def test_legacy_safety_path_is_other(self):
        """The old /{lang}/products/safety/ URL is not part of the new sitemap,
        but if it appears it should NOT classify as safety_hub."""
        c = classify_url("https://capetowndata.com/en/products/safety/")
        assert c.url_type == "other"


# ---------------------------------------------------------------------------
# HTML parsing
# ---------------------------------------------------------------------------


def test_parse_html_extracts_metadata():
    html = """
    <html>
      <head>
        <title>Safety in Sea Point</title>
        <meta name="description" content="Crime statistics and safety tips." />
        <meta name="robots" content="index, follow" />
        <link rel="canonical" href="https://capetowndata.com/en/safety/" />
        <link rel="alternate" hreflang="en" href="https://capetowndata.com/en/safety/" />
        <link rel="alternate" hreflang="de" href="https://capetowndata.com/de/safety/" />
      </head>
      <body></body>
    </html>
    """
    parsed = _parse_html("https://capetowndata.com/en/safety/", html)
    assert parsed["has_noindex"] is False
    assert parsed["canonical_url"] == "https://capetowndata.com/en/safety/"
    assert parsed["canonical_matches_self"] is True
    assert parsed["hreflang_count"] == 2
    assert parsed["title"] == "Safety in Sea Point"
    assert parsed["meta_description"] == "Crime statistics and safety tips."


def test_parse_html_detects_noindex():
    html = '<html><head><meta name="robots" content="noindex, nofollow"></head></html>'
    parsed = _parse_html("https://example.com/", html)
    assert parsed["has_noindex"] is True


def test_parse_html_canonical_mismatch():
    html = (
        '<html><head>'
        '<link rel="canonical" href="https://capetowndata.com/en/safety/" />'
        "</head></html>"
    )
    parsed = _parse_html("https://capetowndata.com/en/about/", html)
    assert parsed["canonical_matches_self"] is False


# ---------------------------------------------------------------------------
# Sitemap fetching + probing
# ---------------------------------------------------------------------------


SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://capetowndata.com/en/</loc></url>
  <url><loc>https://capetowndata.com/en/products/blogpost/140/</loc></url>
  <url><loc>https://capetowndata.com/en/safety/</loc></url>
</urlset>"""


@pytest.mark.asyncio
async def test_fetch_sitemap_urls_flat():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=SITEMAP_XML, headers={"content-type": "application/xml"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        urls = await _fetch_sitemap_urls(client)

    assert urls == [
        "https://capetowndata.com/en/",
        "https://capetowndata.com/en/products/blogpost/140/",
        "https://capetowndata.com/en/safety/",
    ]


SITEMAP_INDEX_XML = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://capetowndata.com/sitemap-posts.xml</loc></sitemap>
</sitemapindex>"""


@pytest.mark.asyncio
async def test_fetch_sitemap_urls_index_recurses():
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url == "https://capetowndata.com/sitemap.xml":
            return httpx.Response(200, text=SITEMAP_INDEX_XML)
        if url == "https://capetowndata.com/sitemap-posts.xml":
            return httpx.Response(200, text=SITEMAP_XML)
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        urls = await _fetch_sitemap_urls(client)

    assert len(urls) == 3


@pytest.mark.asyncio
async def test_probe_one_success():
    import asyncio as _asyncio
    url = "https://capetowndata.com/en/products/blogpost/140/"
    html = (
        "<html><head>"
        "<title>Anchor</title>"
        f'<link rel="canonical" href="{url}" />'
        "</head></html>"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=html, headers={"content-type": "text/html"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        record = await _probe_one(client, url, _asyncio.Semaphore(1), 0.0)

    assert record.http_status == 200
    assert record.classification.url_type == "blogpost"
    assert record.classification.blogpost_id == 140
    assert record.title == "Anchor"
    assert record.canonical_matches_self is True
