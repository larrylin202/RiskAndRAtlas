"""Keeps hazard_features fresh without a separate cron service.

API requests call maybe_refresh_async(). At most once a minute per process it starts a
background thread that claims every feed whose last refresh attempt is older than
INGEST_STALE_MINUTES, and refreshes the claimed feeds. The claim is a single atomic
UPDATE on ingest_runs, so concurrent processes never refresh the same feed twice.
Requests never wait on a feed; they keep serving whatever is already in the table.
"""
import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from flask import current_app
from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert
from ..extensions import db
from ..models import IngestRun
from . import usgs, nifc, rtfi

logger = logging.getLogger(__name__)

SERVICES = {"usgs": usgs, "nifc": nifc, "rtfi": rtfi}

CHECK_INTERVAL_S = 60  # per-process throttle so not every request touches ingest_runs

_next_check = 0.0
_check_lock = threading.Lock()


def _save_run(source, **values):
    stmt = insert(IngestRun).values(source=source, **values)
    db.session.execute(stmt.on_conflict_do_update(index_elements=["source"], set_=values))
    db.session.commit()


def run_source(source):
    """Refresh one feed now and record the outcome in ingest_runs. Returns (seen, changed); re-raises on failure."""
    started = datetime.now(timezone.utc)
    _save_run(source, last_attempt_at=started)
    try:
        seen, changed = SERVICES[source].refresh()
    except Exception as e:
        db.session.rollback()
        _save_run(source, last_error=f"{type(e).__name__}: {e}"[:1000])
        raise
    _save_run(source, last_success_at=started, row_count=seen, last_error=None)
    return seen, changed


def claim_stale_sources(stale_after):
    """Atomically mark every feed not attempted within stale_after as attempted now; return those feeds.

    Keyed on last_attempt_at (not last_success_at) so a failing feed is retried once
    per window instead of on every check, and a refresh in progress isn't claimed again.
    """
    now = datetime.now(timezone.utc)
    stmt = insert(IngestRun).values([{"source": s, "last_attempt_at": now} for s in SERVICES])
    stmt = stmt.on_conflict_do_update(
        index_elements=["source"],
        set_={"last_attempt_at": now},
        where=or_(IngestRun.last_attempt_at.is_(None), IngestRun.last_attempt_at < now - stale_after),
    ).returning(IngestRun.source)
    claimed = db.session.execute(stmt).scalars().all()
    db.session.commit()
    return claimed


def _refresh_in_background(app):
    with app.app_context():
        try:
            stale_after = timedelta(minutes=app.config["INGEST_STALE_MINUTES"])
            for source in claim_stale_sources(stale_after):
                try:
                    seen, changed = run_source(source)
                    logger.info("auto-ingest %s: %d features, %d changed", source, seen, changed)
                except Exception:
                    logger.exception("auto-ingest %s failed", source)
        except Exception:
            # e.g. DB unreachable; the next check (a minute later) tries again
            db.session.rollback()
            logger.exception("auto-ingest check failed")


def maybe_refresh_async():
    """Start a background refresh of stale feeds, at most once per CHECK_INTERVAL_S per process."""
    global _next_check
    app = current_app._get_current_object()
    if not app.config.get("AUTO_INGEST", True):
        return
    with _check_lock:
        if time.monotonic() < _next_check:
            return
        _next_check = time.monotonic() + CHECK_INTERVAL_S
    threading.Thread(target=_refresh_in_background, args=(app,), daemon=True, name="auto-ingest").start()


def feed_status():
    """Per-feed refresh info for /api/health. Raises if the DB is unreachable."""
    stale_after = timedelta(minutes=current_app.config["INGEST_STALE_MINUTES"])
    now = datetime.now(timezone.utc)
    runs = {r.source: r for r in db.session.execute(select(IngestRun)).scalars()}
    status = {}
    for source in SERVICES:
        run = runs.get(source)
        last_success = run.last_success_at if run else None
        status[source] = {
            "last_success_at": last_success.isoformat() if last_success else None,
            "row_count": run.row_count if run else None,
            "last_error": run.last_error if run else None,
            "stale": last_success is None or now - last_success > stale_after,
        }
    return status
