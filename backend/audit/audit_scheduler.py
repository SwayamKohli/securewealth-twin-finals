from __future__ import annotations

import asyncio
import logging

from audit.tamper_monitor import TamperMonitor

logger = logging.getLogger("guardian.audit_scheduler")


class AuditScheduler:

    def __init__(
        self,
        tamper_monitor: TamperMonitor,
        interval_seconds: int = 300,
    ):
        self._monitor = tamper_monitor
        self._interval = interval_seconds

        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:

        if self._running:
            return

        self._running = True

        logger.info(
            "Audit Scheduler started. Interval=%d seconds.",
            self._interval,
        )

        self._task = asyncio.create_task(
            self._run_loop()
        )

    async def stop(self) -> None:

        self._running = False

        if self._task:

            self._task.cancel()

            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info(
            "Audit Scheduler stopped."
        )

    async def _run_loop(self) -> None:

        while self._running:

            try:

                report = self._monitor.run()

                logger.info(
                    "Integrity Check | Status=%s | Checked=%d | Recoveries=%d",
                    report.overall_status,
                    report.checked_records,
                    report.recoveries_succeeded,
                )

            except Exception as exc:

                # A dropped pooled connection (managed Postgres idle timeout)
                # leaves this scheduler's long-lived Session in a broken state.
                # Roll it back so the next cycle gets a fresh connection
                # instead of failing forever.
                logger.warning(
                    "Audit integrity check failed (%s). "
                    "Resetting the session and retrying next cycle.",
                    exc.__class__.__name__,
                )
                self._reset_session()

            await asyncio.sleep(
                self._interval
            )

    def _reset_session(self) -> None:
        """Roll back the monitor's DB session after a connection failure."""
        for attr in ("_audit", "_repo", "_verifier", "_recovery"):
            obj = getattr(self._monitor, attr, None)
            db = getattr(obj, "db", None) or getattr(
                getattr(obj, "_repo", None), "db", None
            )
            if db is not None:
                try:
                    db.rollback()
                except Exception:
                    pass