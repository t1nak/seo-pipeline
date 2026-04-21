"""Probe old-domain URLs for redirect health.

The Cloudflare "Super Bot Fight Mode" challenge on es-capetown.com silently
served Googlebot a 403 with `cf-mitigated: challenge` for two months after the
migration, which collapsed traffic from 18k to 4k weekly clicks. Catching any
recurrence of that pattern is the primary purpose of this job.

Verdict codes:
  CLEAN         — single 301/302 → 200 on the new domain (or 2 hops OK)
  CHAIN         — more than 2 hops before reaching 200
  BROKEN_404    — chain terminates in 404
  BROKEN_5XX    — chain terminates in 5xx
  BLOCKED       — any hop returns `cf-mitigated: challenge` (critical!)
  NO_REDIRECT   — old URL returns 200 directly (redirect stripped)
  OTHER         — catch-all
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx

from ..config import GOOGLEBOT_UA, LOCALES, PRIMARY_DOMAIN
from ..models import RedirectProbe
from ._runlog import JobContext, raise_alert, run_job

logger = logging.getLogger(__name__)

MAX_HOPS = 5
REQUEST_TIMEOUT = 15.0


TOP_20_LEGACY_URLS: tuple[str, ...] = (
    "https://es-capetown.com/en/products/blogpost/140/",
    "https://es-capetown.com/de/products/blogpost/140/",
    "https://es-capetown.com/es/products/blogpost/140/",
    "https://es-capetown.com/fr/products/blogpost/140/",
    "https://es-capetown.com/nl/products/blogpost/140/",
    "https://es-capetown.com/it/products/blogpost/140/",
    "https://es-capetown.com/en/products/safety/",
    "https://es-capetown.com/de/products/safety/",
    "https://es-capetown.com/es/products/safety/",
    "https://es-capetown.com/en/",
    "https://es-capetown.com/de/",
    "https://es-capetown.com/es/",
    "https://es-capetown.com/fr/",
    "https://es-capetown.com/nl/",
    "https://es-capetown.com/it/",
    "https://es-capetown.com/ja/",
    "https://es-capetown.com/pt/",
    "https://es-capetown.com/ru/",
    "https://es-capetown.com/",
    "https://www.es-capetown.com/",
)


def _legacy_safety_paths() -> tuple[str, ...]:
    return tuple(
        f"https://es-capetown.com/{lang}/products/safety/" for lang in LOCALES
    ) + tuple(
        f"https://capetowndata.com/{lang}/products/safety/" for lang in LOCALES
    )


def probe_urls() -> list[str]:
    """Return the full set of URLs to probe (deduplicated, stable order)."""
    seen: dict[str, None] = {}
    for url in (*TOP_20_LEGACY_URLS, *_legacy_safety_paths()):
        seen.setdefault(url, None)
    return list(seen.keys())


@dataclass
class Hop:
    url: str
    status: int
    location: str | None = None
    cf_mitigated: bool = False

    def to_json(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "status": self.status,
            "location": self.location,
            "cf_mitigated": self.cf_mitigated,
        }


@dataclass
class ProbeResult:
    old_url: str
    chain: list[Hop] = field(default_factory=list)
    final_url: str | None = None
    final_status: int | None = None
    cf_mitigated: bool = False
    verdict: str = "OTHER"

    @property
    def hop_count(self) -> int:
        return len(self.chain)


def classify(result: ProbeResult) -> str:
    """Assign a verdict to a completed probe."""
    if result.cf_mitigated:
        return "BLOCKED"

    if result.final_status is None:
        return "OTHER"

    if not result.chain:
        return "OTHER"

    first = result.chain[0]
    redirected = any(300 <= h.status < 400 for h in result.chain)

    if not redirected and first.status == 200:
        return "NO_REDIRECT"

    if 500 <= result.final_status < 600:
        return "BROKEN_5XX"

    if result.final_status == 404:
        return "BROKEN_404"

    if result.final_status == 200:
        # Chains with more than 2 redirect hops are allowed but flagged.
        redirect_hops = sum(1 for h in result.chain if 300 <= h.status < 400)
        if redirect_hops > 2:
            return "CHAIN"
        return "CLEAN"

    return "OTHER"


async def probe_once(client: httpx.AsyncClient, url: str) -> ProbeResult:
    """Follow the redirect chain by hand so every hop is recorded."""
    result = ProbeResult(old_url=url)
    current = url

    for _ in range(MAX_HOPS + 1):
        try:
            resp = await client.get(current, follow_redirects=False)
        except httpx.HTTPError as exc:
            logger.warning("Request error for %s: %s", current, exc)
            result.verdict = "OTHER"
            return result

        cf_mitigated_header = resp.headers.get("cf-mitigated", "").lower()
        cf_mitigated = "challenge" in cf_mitigated_header

        hop = Hop(
            url=current,
            status=resp.status_code,
            location=resp.headers.get("location"),
            cf_mitigated=cf_mitigated,
        )
        result.chain.append(hop)

        if cf_mitigated:
            result.cf_mitigated = True
            result.final_url = current
            result.final_status = resp.status_code
            result.verdict = "BLOCKED"
            return result

        if 300 <= resp.status_code < 400 and hop.location:
            current = httpx.URL(current).join(hop.location).human_repr()
            continue

        result.final_url = current
        result.final_status = resp.status_code
        break
    else:
        # Exceeded MAX_HOPS
        result.final_url = current
        result.final_status = result.chain[-1].status if result.chain else None
        result.verdict = "CHAIN"
        return result

    result.verdict = classify(result)
    return result


async def _probe_all(urls: list[str]) -> list[ProbeResult]:
    headers = {"User-Agent": GOOGLEBOT_UA, "Accept": "text/html,*/*"}
    async with httpx.AsyncClient(
        http2=True,
        timeout=REQUEST_TIMEOUT,
        headers=headers,
        verify=True,
    ) as client:
        results = []
        # Serial with 1 req/sec pacing — this is monitoring, not load testing.
        for url in urls:
            results.append(await probe_once(client, url))
            await asyncio.sleep(1.0)
        return results


def _persist(ctx: JobContext, results: list[ProbeResult]) -> None:
    now = datetime.now(timezone.utc)
    for r in results:
        ctx.session.add(
            RedirectProbe(
                old_url=r.old_url,
                probed_at=now,
                hop_count=r.hop_count,
                chain=[h.to_json() for h in r.chain],
                final_url=r.final_url,
                final_status=r.final_status,
                cf_mitigated=r.cf_mitigated,
                verdict=r.verdict,
            )
        )
    ctx.rows_written = len(results)


def _raise_alerts(ctx: JobContext, results: list[ProbeResult]) -> None:
    blocked = [r for r in results if r.verdict == "BLOCKED"]
    if blocked:
        ctx.downgrade_to_partial(
            f"{len(blocked)} URL(s) blocked by Cloudflare challenge"
        )
        for r in blocked:
            raise_alert(
                ctx,
                severity="critical",
                message=(
                    f"BLOCKED: {r.old_url} returned cf-mitigated: challenge. "
                    "The Cloudflare Super Bot Fight Mode pattern has resurfaced — "
                    "check the old zone config immediately. Do NOT touch the GSC "
                    "Change of Address."
                ),
            )

    top_broken = [
        r for r in results
        if r.old_url in TOP_20_LEGACY_URLS and r.verdict not in ("CLEAN", "BLOCKED")
    ]
    for r in top_broken:
        raise_alert(
            ctx,
            severity="critical",
            message=f"Top-20 URL {r.old_url} verdict is {r.verdict} (was CLEAN).",
        )


def run() -> None:
    with run_job("redirect_health") as ctx:
        urls = probe_urls()
        logger.info("Probing %d URLs", len(urls))
        results = asyncio.run(_probe_all(urls))
        _persist(ctx, results)
        _raise_alerts(ctx, results)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
