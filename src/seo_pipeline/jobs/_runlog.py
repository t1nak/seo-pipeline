"""Shared run_log + alerts helpers.

Every job writes a row to run_log on start, then updates status/rows_written/
error on finish. Errors propagate — they are never silently swallowed.
"""

from __future__ import annotations

import logging
import sys
import traceback
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

from sqlalchemy.orm import Session

from ..db import session_scope
from ..models import Alert, RunLog

logger = logging.getLogger(__name__)


class JobContext:
    """Tracks a single job invocation.

    Usage:
        with run_job("redirect_health") as ctx:
            ctx.rows_written = do_work(ctx)
            if something_bad:
                ctx.downgrade_to_partial("one URL blocked")
                raise_alert(ctx, severity="critical", message="…")
    """

    def __init__(self, run_log: RunLog, session: Session):
        self.run_log = run_log
        self.session = session
        self.rows_written = 0
        self._status = "running"

    @property
    def job_name(self) -> str:
        return self.run_log.job_name

    @property
    def id(self) -> int | None:
        return self.run_log.id

    def downgrade_to_partial(self, reason: str) -> None:
        if self._status != "failed":
            self._status = "partial"
            prior = self.run_log.error_message or ""
            suffix = reason if not prior else f"{prior}; {reason}"
            self.run_log.error_message = suffix

    def set_status(self, status: str) -> None:
        self._status = status


@contextmanager
def run_job(job_name: str) -> Iterator[JobContext]:
    started = datetime.now(timezone.utc)
    with session_scope() as session:
        run_log = RunLog(
            run_started_at=started,
            job_name=job_name,
            status="running",
        )
        session.add(run_log)
        session.flush()
        ctx = JobContext(run_log, session)

        try:
            yield ctx
        except Exception as exc:
            ctx._status = "failed"
            run_log.error_message = f"{type(exc).__name__}: {exc}"
            logger.error(
                "Job %s failed: %s\n%s",
                job_name,
                exc,
                traceback.format_exc(),
            )
            raise_alert(
                ctx,
                severity="warning",
                message=f"Job {job_name} failed: {type(exc).__name__}: {exc}",
            )
            print(traceback.format_exc(), file=sys.stderr)
            raise
        finally:
            run_log.run_finished_at = datetime.now(timezone.utc)
            run_log.status = ctx._status if ctx._status != "running" else "success"
            run_log.rows_written = ctx.rows_written
            session.add(run_log)


def raise_alert(ctx: JobContext, *, severity: str, message: str) -> None:
    """Insert an alert row tied to the current run.

    Severity must be one of: info, warning, critical.
    """
    if severity not in {"info", "warning", "critical"}:
        raise ValueError(f"Invalid severity: {severity}")

    alert = Alert(
        created_at=datetime.now(timezone.utc),
        severity=severity,
        job_name=ctx.job_name,
        message=message,
        run_log_id=ctx.id,
    )
    ctx.session.add(alert)
    logger.warning("[%s] %s alert: %s", ctx.job_name, severity, message)
