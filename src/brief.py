"""Brief step of the SEO keyword pipeline.

For each HDBSCAN cluster, generates a German content brief and writes it
as Markdown to `output/briefings/cluster_{nn}.md`.

The brief structure follows what an editor would expect for a B2B SaaS blog:

  * Arbeitstitel (working title)
  * Zielgruppe (audience persona)
  * Schmerzpunkt (pain point) and Ziel (goal of the article)
  * Suchintention (search intent classification)
  * H1 to H3 outline
  * Empfohlene Wortanzahl (recommended word count)
  * Drei Wettbewerbs-URLs als Benchmarks (three benchmark URLs to study)
  * Call to action

Real LLM call in default mode. `--dry-run` writes a stub per cluster
(useful for offline iteration on the rest of the pipeline).

Three providers, switchable via `--provider`:

  api      anthropic SDK + ANTHROPIC_API_KEY env var.
           Separate billing on the Anthropic API account. Reproducible
           in CI, deployable to serverless. Supports `--model <id>` and
           prompt caching for the stable system prompt.

  openai   openai SDK + OPENAI_API_KEY env var.
           Separate billing on the OpenAI account. CI- and serverless-
           safe. Supports `--model <id>`. Uses standard chat-completion
           endpoint with system + user messages.

  max      claude-agent-sdk + local Claude Code CLI session.
           Billed via Claude Max / Pro subscription. Model id is
           inherited from the Claude Code session and cannot be pinned;
           passing `--model` errors out. No prompt caching (SDK
           limitation). Local only because GitHub-Action runners have
           no logged-in CLI.

Recommendation: `max` for solo development, `api` (or `openai`) for CI
and deploys. See docs/decisions.md (ADR-11) for the trade-off.

CLI:
    python -m src.brief                                    api + ANTHROPIC_API_KEY, default model
    python -m src.brief --provider max                     Max subscription via local CC session
    python -m src.brief --provider openai                  openai + OPENAI_API_KEY, default model
    python -m src.brief --provider api --model claude-opus-4-7
    python -m src.brief --provider openai --model gpt-5
    python -m src.brief --dry-run                          stub mode, no LLM call
    python -m src.brief --cluster 5                        regenerate just one cluster (0-based)
"""
from __future__ import annotations

import argparse
import asyncio
import logging
from src.logging_config import setup_logging
import os
import sys
from pathlib import Path

import pandas as pd

from src.config import settings
from src.retry import with_retry

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
BRIEFINGS = OUT / "briefings"
PROFILES_CSV = OUT / "clustering" / "cluster_profiles.csv"
LABELED_CSV = OUT / "clustering" / "keywords_labeled.csv"

DEFAULT_API_MODEL = "claude-sonnet-4-6"
DEFAULT_OPENAI_MODEL = "gpt-5"
MAX_TOKENS = settings.brief_max_tokens

SYSTEM_PROMPT = """Du bist Senior Content Strategist für den deutschen B2B SaaS Markt.
Spezialgebiet: Personaldienstleistung, Zeitarbeit, Recruiting Software, Compliance.

Deine Aufgabe: pro Keyword Cluster einen Content Brief für einen Blog Artikel erstellen,
der für Google rankt und gleichzeitig echte Kaufinteressenten anspricht.

Format des Briefs (immer Markdown, immer Deutsch, immer in dieser Reihenfolge):

# {Arbeitstitel}

**Hauptkeyword:** {hauptkeyword}
**Nebenkeywords:** {3 bis 7 nebenkeywords}
**Suchintention:** {commercial / informational / mixed}, {1 Satz Begründung}
**Empfohlene Wortanzahl:** {1500 bis 3500}

## Zielgruppe

{1 Satz Persona, konkrete Rolle und Firmengröße}

## Schmerzpunkt

{2 bis 3 Sätze, was diese Person nachts wachhält}

## Ziel des Artikels

{1 Satz, was der Leser nach dem Lesen tun oder verstanden haben soll}

## Outline

- H1: {Titel}
- H2: {Section 1}
  - H3: ...
- H2: {Section 2}
  - H3: ...
{4 bis 7 H2 Abschnitte mit jeweils 1 bis 4 H3 Unterpunkten}

## Benchmark URLs

1. {URL eines direkten Wettbewerbers oder eines hoch rankenden Artikels} — {warum relevant}
2. ...
3. ...

## Call to Action

{1 konkrete Aktion, idealerweise mit Bezug zu zvoove Produkten}

Schreibe pragmatisch, nicht akademisch. Keine Floskeln. Keine KI Erkennungsmerkmale
wie Gedankenstriche. Nutze Komma, Doppelpunkt, oder neuen Satz.

Wichtig: Beginne deine Antwort SOFORT mit der Zeile `# {Arbeitstitel}`. Kein
einleitender Satz, kein Vorwort, keine Beschreibung deines Vorgehens, kein
'Ich recherchiere...'. Erste Zeichen der Antwort sind `# `."""


def _strip_preamble(text: str) -> str:
    """Drop anything before the first markdown H1 line.

    Defensive: even with the system prompt instruction above, an agent-style
    provider may still emit a narration line like 'Ich recherchiere ...'
    before the actual brief. We anchor on the first '# ' that starts a line.
    """
    idx = text.find("\n# ")
    if idx >= 0:
        return text[idx + 1:]
    if text.lstrip().startswith("# "):
        return text.lstrip()
    return text


def _user_prompt(cluster_id: int, label_de: str, profile: dict, top_kw: list[str]) -> str:
    """Per-cluster prompt assembled from the cluster profile and the top keywords."""
    return (
        f"CLUSTER {cluster_id + 1}: {label_de}\n\n"
        f"Statistiken:\n"
        f"  Anzahl Keywords im Cluster: {profile['n_keywords']}\n"
        f"  Gesamt Suchvolumen pro Monat: {profile['total_sv']}\n"
        f"  Mittlere Keyword Difficulty: {profile['mean_kd']}\n"
        f"  Mittlerer CPC: {profile['mean_cpc']} EUR\n"
        f"  Anteil kommerzielle Keywords: {profile['pct_commercial']} Prozent\n\n"
        f"Top Keywords nach Suchvolumen:\n"
        + "\n".join(f"  - {kw}" for kw in top_kw)
        + "\n\nErstelle einen Content Brief für diesen Cluster nach dem oben definierten Format."
    )


def _stub_brief(cluster_id: int, label_de: str, top_kw: list[str]) -> str:
    """Used in --dry-run mode and as fallback when the LLM call fails."""
    return (
        f"# Cluster {cluster_id + 1}: {label_de}\n\n"
        f"**Status:** Stub (dry run mode, kein LLM Aufruf).\n\n"
        f"**Top Keywords:**\n"
        + "\n".join(f"- {kw}" for kw in top_kw[:5])
        + f"\n\nFür einen vollständigen Brief mit `python -m src.brief --cluster "
        f"{cluster_id}` neu generieren.\n"
    )


def _looks_like_real_brief(path: Path) -> bool:
    """Heuristic: a real brief contains the structured sections, a stub does not."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return ("**Hauptkeyword:**" in text and "## Outline" in text
            and "Status:** Stub" not in text)


def _short_path(path: Path) -> str:
    """Path relative to ROOT if possible, else just the file name. For logs."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return path.name


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------


class BriefProvider:
    """Abstract provider. Concrete implementations: ApiKeyProvider (Anthropic),
    OpenAIProvider, AgentSdkProvider (Claude Code subscription).

    Adding a new provider: subclass BriefProvider, set `name`, implement
    `generate(system, user) -> str`, register in `make_provider`.
    """

    name: str = "abstract"

    def generate(self, system: str, user: str) -> str:
        raise NotImplementedError


class ApiKeyProvider(BriefProvider):
    """Anthropic SDK + API key. CI-safe path, supports model selection and prompt caching."""

    name = "api"

    def __init__(self, model: str):
        try:
            from anthropic import Anthropic
        except ImportError:
            sys.exit("anthropic SDK not installed. `pip install anthropic`, "
                     "or switch to --provider max, or use --dry-run.")
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            sys.exit("ANTHROPIC_API_KEY not set. Export it, "
                     "or switch to --provider max (uses local Claude Code session), "
                     "or use --dry-run.")
        self.model = model
        self._client = Anthropic(api_key=api_key)

    @with_retry()
    def generate(self, system: str, user: str) -> str:
        msg = self._client.messages.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            system=[{
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text


class OpenAIProvider(BriefProvider):
    """OpenAI SDK + API key. CI-safe path, supports model selection.

    Standard chat-completion request with system + user messages. Prompt
    caching on the OpenAI side happens automatically for prefixes longer
    than 1024 tokens (no explicit field needed).
    """

    name = "openai"

    def __init__(self, model: str):
        try:
            from openai import OpenAI
        except ImportError:
            sys.exit("openai SDK not installed. `pip install openai`, "
                     "or switch to --provider api / max, or use --dry-run.")
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            sys.exit("OPENAI_API_KEY not set. Export it, "
                     "or switch to --provider api / max, "
                     "or use --dry-run.")
        self.model = model
        self._client = OpenAI(api_key=api_key)

    @with_retry()
    def generate(self, system: str, user: str) -> str:
        msg = self._client.chat.completions.create(
            model=self.model,
            max_completion_tokens=MAX_TOKENS,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return msg.choices[0].message.content or ""


class AgentSdkProvider(BriefProvider):
    """claude-agent-sdk wrapping the local Claude Code CLI session.

    Billed against the user's Claude Max / Pro subscription. Local only:
    GitHub-Action runners have no logged-in CLI, so this provider cannot
    run in CI. Model id is inherited from the active Claude Code session
    and cannot be overridden. No prompt caching exposed by the SDK.
    """

    name = "max"

    def __init__(self) -> None:
        try:
            from claude_agent_sdk import (
                query, ClaudeAgentOptions, AssistantMessage,
            )
        except ImportError:
            sys.exit("claude-agent-sdk not installed. `pip install claude-agent-sdk` "
                     "(requires Python >=3.10), or switch to --provider api, "
                     "or use --dry-run.")
        self._query = query
        self._options_cls = ClaudeAgentOptions
        self._assistant_cls = AssistantMessage

    def generate(self, system: str, user: str) -> str:
        async def _run() -> str:
            text = ""
            async for msg in self._query(
                prompt=user,
                options=self._options_cls(
                    system_prompt=system,
                    allowed_tools=[],  # pure text output, no tool use
                ),
            ):
                if isinstance(msg, self._assistant_cls):
                    for block in msg.content:
                        if hasattr(block, "text"):
                            text += block.text
            return text

        return asyncio.run(_run())


def make_provider(name: str, model: str | None) -> BriefProvider:
    if name == "api":
        return ApiKeyProvider(model=model or DEFAULT_API_MODEL)
    if name == "openai":
        return OpenAIProvider(model=model or DEFAULT_OPENAI_MODEL)
    if name == "max":
        if model is not None:
            sys.exit(
                "--model is not supported with --provider max. The model is "
                "inherited from the active Claude Code session. Either drop "
                "--model, or switch to --provider api or --provider openai."
            )
        return AgentSdkProvider()
    sys.exit(f"unknown provider: {name!r}. choose 'api', 'openai', or 'max'.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run(provider_name: str = "api", model: str | None = None,
        dry_run: bool = False, cluster_filter: int | None = None) -> None:
    if not PROFILES_CSV.exists() or not LABELED_CSV.exists():
        sys.exit(f"missing inputs. Expected {PROFILES_CSV.relative_to(ROOT)} and "
                 f"{LABELED_CSV.relative_to(ROOT)}. Run `python -m src.cluster` first.")

    BRIEFINGS.mkdir(parents=True, exist_ok=True)
    profiles = pd.read_csv(PROFILES_CSV)
    labeled = pd.read_csv(LABELED_CSV)

    provider: BriefProvider | None = None
    if not dry_run:
        provider = make_provider(provider_name, model)
        suffix = f" model={model}" if (model and provider.name == "api") else ""
        logger.info("provider=%s%s", provider.name, suffix)

    n_ok = n_fail = 0
    for _, row in profiles.iterrows():
        cid = int(row["cluster_id"])
        if cid == -1:
            continue  # skip noise cluster
        if cluster_filter is not None and cid != cluster_filter:
            continue

        label_de = row["label_de"]
        top_kw = labeled.loc[labeled["hdb"] == cid].sort_values(
            "search_volume", ascending=False).head(10)["keyword"].tolist()
        out_path = BRIEFINGS / f"cluster_{cid + 1:02d}.md"

        if dry_run:
            # Safety: do not overwrite a real, structured brief with a stub.
            # If the user wanted to reset, they can delete the file first.
            if _looks_like_real_brief(out_path):
                logger.info("(dry-run) skipping %s, real brief in place", out_path.name)
                continue
            out_path.write_text(_stub_brief(cid, label_de, top_kw))
            logger.info("(dry-run) wrote %s", _short_path(out_path))
            n_ok += 1
            continue

        try:
            assert provider is not None  # for type checker; set above when not dry_run
            text = provider.generate(
                SYSTEM_PROMPT,
                _user_prompt(cid, label_de, row.to_dict(), top_kw),
            )
            text = _strip_preamble(text)
            out_path.write_text(text)
            logger.info("wrote %s (%d chars, via %s)",
                        _short_path(out_path), len(text), provider.name)
            n_ok += 1
        except Exception as exc:
            logger.error("cluster %d FAILED: %s", cid, exc)
            out_path.write_text(_stub_brief(cid, label_de, top_kw))
            n_fail += 1

    logger.info("done. ok=%d failed=%d", n_ok, n_fail)


def main() -> None:
    setup_logging()
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--provider", choices=["api", "openai", "max"], default=None,
                   help="api: anthropic SDK + ANTHROPIC_API_KEY (CI-safe). "
                        "openai: openai SDK + OPENAI_API_KEY (CI-safe). "
                        "max: claude-agent-sdk + local Claude Code session (Max-Abo, local only). "
                        f"Default from settings: {settings.brief_provider}.")
    p.add_argument("--model", default=None,
                   help=f"model id, valid with --provider api or openai. "
                        f"Provider defaults: api={DEFAULT_API_MODEL}, openai={DEFAULT_OPENAI_MODEL}. "
                        f"Settings default: {settings.brief_model or 'provider default'}.")
    p.add_argument("--dry-run", action="store_true",
                   help="skip LLM calls, write stubs (no provider needed).")
    p.add_argument("--cluster", type=int, default=None,
                   help="only generate this cluster id (0-based).")
    args = p.parse_args()
    # CLI > settings > defaults. If CLI flag is None, fall back to settings.
    if args.provider is None:
        args.provider = settings.brief_provider
    if args.model is None:
        args.model = settings.brief_model
    run(provider_name=args.provider, model=args.model,
        dry_run=args.dry_run, cluster_filter=args.cluster)


if __name__ == "__main__":
    main()
