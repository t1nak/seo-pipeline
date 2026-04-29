"""Single place that configures the root logger for the pipeline.

The default format is structured but human-readable:

    2026-04-29 12:34:56 | cluster.embed     | INFO  | encoding 500 keywords

Every module gets its logger via `logger = logging.getLogger(__name__)`,
which produces names like `src.cluster`, `src.brief`, `src.briefs_html`.
The `__name__` is shortened on display so the prefix in the formatter
stays compact.

Verbosity comes from `settings.log_level` (env var `PIPELINE_LOG_LEVEL`).
Default INFO. Set DEBUG for full per-step traces, WARNING to silence the
ok-path output.

Usage in the entry point:

    from src.logging_config import setup_logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("starting")

Modules just need:

    import logging
    logger = logging.getLogger(__name__)
    logger.info("doing work")
"""
from __future__ import annotations

import logging
import sys

from src.config import settings


_CONFIGURED = False


class _ShortNameFilter(logging.Filter):
    """Truncate `src.foo.bar` to `foo.bar` for cleaner formatter output."""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.name.startswith("src."):
            record.short_name = record.name[len("src."):]
        else:
            record.short_name = record.name
        return True


def setup_logging(level: str | int | None = None) -> None:
    """Configure the root logger. Idempotent, safe to call repeatedly.

    Args:
        level: optional override for the log level. Falls back to
               `settings.log_level` (env var `PIPELINE_LOG_LEVEL`,
               default INFO).
    """
    global _CONFIGURED
    if _CONFIGURED and level is None:
        return

    chosen = level if level is not None else settings.log_level
    if isinstance(chosen, str):
        chosen = chosen.upper()

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s | %(short_name)-18s | %(levelname)-5s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    handler.addFilter(_ShortNameFilter())

    root = logging.getLogger()
    # Drop any handlers attached by libraries before we got here (e.g. notebooks)
    for h in list(root.handlers):
        root.removeHandler(h)
    root.addHandler(handler)
    root.setLevel(chosen)

    # Tame noisy library loggers
    for noisy in ("urllib3", "httpx", "httpcore", "anthropic", "openai",
                  "sentence_transformers", "transformers"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _CONFIGURED = True
