"""Data retention purge job.

Deletes transcripts older than RETENTION_DAYS (if >0) on a scheduled run.
Run periodically via cron / Kubernetes CronJob.
"""
from __future__ import annotations

from datetime import datetime, UTC, timedelta
from sqlalchemy import delete
from persistence import transcripts, SessionLocal
from config import get_settings
from metrics import transcripts_purged_total
import structlog

logger = structlog.get_logger().bind(component="retention")


def purge_once(now: datetime | None = None) -> int:
    settings = get_settings()
    days = settings.retention_days
    if not days or days <= 0:
        return 0
    cutoff = (now or datetime.now(UTC)) - timedelta(days=days)
    with SessionLocal() as session:
        result = session.execute(
            delete(transcripts).where(transcripts.c.created_at < cutoff)
        )
        deleted = result.rowcount or 0
        if deleted:
            transcripts_purged_total.inc(deleted)
        session.commit()
    logger.info("retention_purge", deleted=deleted, cutoff=cutoff.isoformat())
    return deleted


if __name__ == "__main__":  # pragma: no cover
    purge_once()
