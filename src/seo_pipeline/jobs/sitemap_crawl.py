"""Fetch the capetowndata.com sitemap and probe every URL.

Records HTTP status, response time, title, meta description, canonical,
hreflang count, and whether the page carries a `noindex` directive. Classifies
each URL by shape (language_root / blogpost / safety_hub / safety_subpage /
other) so the dashboard can break metrics down by page type.

Rows are append-only so we can track drift over time.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from ..config import GOOGLEBOT_UA, LOCALES, PRIMARY_DOMAIN, load_settings
from ..models import SitemapProbe
from ._runlog import JobContext, raise_alert, run_job

logger = logging.getLogger(__name__)

SITEMAP_URL = f"https://{PRIMARY_DOMAIN}/sitemap.xml"
REQUEST_TIMEOUT = 20.0
WEEK_OVER_WEEK_DROP_THRESHOLD = 0.05  # 5%


_LANG_ALT = "|".join(LOCALES)
_LANGUAGE_ROOT_RE = re.compile(rf"^/({_LANG_ALT})/?$")
_BLOGPOST_RE = re.compile(rf"^/({_LANG_ALT})/products/blogpost/(\d+)/?$")
_SAFETY_HUB_RE = re.compile(rf"^/({_LANG_ALT})/safety/?$")
_SAFETY_SUBPAGE_RE = re.compile(rf"^/({_LANG_ALT})/safety/[^/]+/?.*$")


@dataclass
class Classification:
    url_type: str
    locale: str | None = None
    blogpost_id: int | None = None


def classify_url(url: str) -> Classification:
    path = urlparse(url).path or "/"
    if not path.endswith("/"):
        path = path + "/"

    if m := _LANGUAGE_ROOT_RE.match(path):
        return Classification("language_root", locale=m.group(1))
    if m := _BLOGPOST_RE.match(path):
        return Classification(
            "blogpost", locale=m.group(1), blogpost_id=int(m.group(2))
        )
    if m := _SAFETY_HUB_RE.match(path):
        return Classification("safety_hub", locale=m.group(1))
    if m := _SAFETY_SUBPAGE_RE.match(path):
        return Classification("safety_subpage", locale=m.group(1))

    # Try to extract a locale prefix even for "other" URLs.
    locale_match = re.match(rf"^/({_LANG_ALT})/", path)
    locale = locale_match.group(1) if locale_match else None
    return Classification("other", locale=locale)


@dataclass
class ProbeRecord:
    url: str
    classification: Classification
    probed_at: datetime
    http_status: int | None
    response_time_ms: int | None
    has_noindex: bool = False
    canonical_url: str | None = None
    canonical_matches_self: bool = False
    hreflang_count: int = 0
    title: str | None = None
    meta_description: str | None = None


async def _fetch_sitemap_urls(client: httpx.AsyncClient) -> list[str]:
    resp = await client.get(SITEMAP_URL, follow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "xml")

    # Sitemap index? Recurse.
    sitemap_tags = soup.find_all("sitemap")
    if sitemap_tags:
        urls: list[str] = []
        for s in sitemap_tags:
            loc = s.find("loc")
            if loc is None or not loc.text:
                continue
            child = await client.get(loc.text, follow_redirects=True)
            child.raise_for_status()
            child_soup = BeautifulSoup(child.text, "xml")
            urls.extend(
                u.find("loc").text for u in child_soup.find_all("url")
                if u.find("loc") is not None and u.find("loc").text
            )
        return urls

    return [
        u.find("loc").text for u in soup.find_all("url")
        if u.find("loc") is not None and u.find("loc").text
    ]


def _parse_html(url: str, html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")

    has_noindex = False
    for meta in soup.find_all("meta"):
        name = (meta.get("name") or "").lower()
        if name == "robots":
            content = (meta.get("content") or "").lower()
            if "noindex" in content:
                has_noindex = True
                break

    canonical_tag = soup.find("link", rel="canonical")
    canonical_url = canonical_tag.get("href") if canonical_tag else None

    hreflang_count = sum(
        1 for link in soup.find_all("link", rel="alternate")
        if link.get("hreflang")
    )

    title_tag = soup.find("title")
    title = title_tag.text.strip() if title_tag and title_tag.text else None

    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = (
        meta_desc_tag.get("content", "").strip() if meta_desc_tag else None
    )

    return {
        "has_noindex": has_noindex,
        "canonical_url": canonical_url,
        "canonical_matches_self": bool(canonical_url) and canonical_url.rstrip("/") == url.rstrip("/"),
        "hreflang_count": hreflang_count,
        "title": title,
        "meta_description": meta_description,
    }


async def _probe_one(
    client: httpx.AsyncClient, url: str, semaphore: asyncio.Semaphore, min_interval: float
) -> ProbeRecord:
    cls = classify_url(url)
    now = datetime.now(timezone.utc)

    async with semaphore:
        start = time.perf_counter()
        try:
            resp = await client.get(url, follow_redirects=True)
        except httpx.HTTPError as exc:
            logger.warning("Fetch failed for %s: %s", url, exc)
            return ProbeRecord(
                url=url,
                classification=cls,
                probed_at=now,
                http_status=None,
                response_time_ms=None,
            )
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        record = ProbeRecord(
            url=url,
            classification=cls,
            probed_at=now,
            http_status=resp.status_code,
            response_time_ms=elapsed_ms,
        )

        ctype = resp.headers.get("content-type", "")
        if resp.status_code == 200 and "html" in ctype:
            parsed = _parse_html(url, resp.text)
            record.has_noindex = parsed["has_noindex"]
            record.canonical_url = parsed["canonical_url"]
            record.canonical_matches_self = parsed["canonical_matches_self"]
            record.hreflang_count = parsed["hreflang_count"]
            record.title = parsed["title"]
            record.meta_description = parsed["meta_description"]

        # Pace per host: enforce min_interval between concurrent-slot releases.
        await asyncio.sleep(min_interval)
        return record


async def _probe_all(urls: list[str]) -> list[ProbeRecord]:
    settings = load_settings()
    headers = {"User-Agent": GOOGLEBOT_UA, "Accept": "text/html,*/*"}
    semaphore = asyncio.Semaphore(settings.sitemap_concurrency)
    min_interval = 1.0 / settings.sitemap_rps if settings.sitemap_rps > 0 else 0

    async with httpx.AsyncClient(
        http2=True,
        timeout=REQUEST_TIMEOUT,
        headers=headers,
    ) as client:
        return await asyncio.gather(
            *(_probe_one(client, u, semaphore, min_interval) for u in urls)
        )


def _persist(ctx: JobContext, records: list[ProbeRecord]) -> None:
    for r in records:
        ctx.session.add(
            SitemapProbe(
                url=r.url,
                locale=r.classification.locale,
                url_type=r.classification.url_type,
                blogpost_id=r.classification.blogpost_id,
                probed_at=r.probed_at,
                http_status=r.http_status,
                response_time_ms=r.response_time_ms,
                has_noindex=r.has_noindex,
                canonical_url=r.canonical_url,
                canonical_matches_self=r.canonical_matches_self,
                hreflang_count=r.hreflang_count,
                title=r.title,
                meta_description=r.meta_description,
            )
        )
    ctx.rows_written = len(records)


def _check_wow_drop(ctx: JobContext, new_count: int) -> None:
    """Warn if the sitemap URL count has dropped >5% week over week."""
    from sqlalchemy import func, select
    from ..models import SitemapProbe as SP

    last_week_counts = ctx.session.execute(
        select(func.date(SP.probed_at), func.count(func.distinct(SP.url)))
        .group_by(func.date(SP.probed_at))
        .order_by(func.date(SP.probed_at).desc())
        .limit(8)
    ).all()

    # Skip the run we just wrote (today). Compare today with ~7 days ago.
    if len(last_week_counts) < 2:
        return
    prior_count = last_week_counts[-1][1]
    if prior_count == 0:
        return
    drop = (prior_count - new_count) / prior_count
    if drop > WEEK_OVER_WEEK_DROP_THRESHOLD:
        raise_alert(
            ctx,
            severity="warning",
            message=(
                f"Sitemap URL count dropped {drop:.1%} week-over-week "
                f"(was {prior_count}, now {new_count})."
            ),
        )


def run() -> None:
    with run_job("sitemap_crawl") as ctx:
        urls = asyncio.run(_fetch_sitemap_urls_wrapper())
        logger.info("Fetched %d URLs from sitemap", len(urls))
        records = asyncio.run(_probe_all(urls))
        _persist(ctx, records)
        _check_wow_drop(ctx, new_count=len(urls))


async def _fetch_sitemap_urls_wrapper() -> list[str]:
    headers = {"User-Agent": GOOGLEBOT_UA, "Accept": "application/xml,*/*"}
    async with httpx.AsyncClient(http2=True, timeout=REQUEST_TIMEOUT, headers=headers) as client:
        return await _fetch_sitemap_urls(client)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
