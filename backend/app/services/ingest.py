import json
from datetime import datetime, timezone
from sqlalchemy import func, delete
from sqlalchemy.dialects.postgresql import insert
from ..extensions import db
from ..models import HazardFeature

# Postgres caps a statement at 65,535 bind parameters; ~7 per row
BATCH_SIZE = 1000


def from_epoch_ms(value):
    """Convert an epoch-milliseconds timestamp (USGS, ArcGIS) to an aware datetime."""
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc)


def upsert_features(source, hazard_type, records):
    """Insert or update one feed's features, then delete rows the feed no longer returns.

    Each record is a dict with keys: source_id, title, properties, geometry
    (a GeoJSON geometry dict) and observed_at (datetime or None).
    Returns the number of rows written.
    """
    now = datetime.now(timezone.utc)

    # ON CONFLICT can't touch the same row twice in one statement, so dedupe first
    unique = {}
    for r in records:
        if r.get("geometry") and r.get("source_id") is not None:
            unique[str(r["source_id"])] = r

    rows = [{
        "source": source,
        "source_id": source_id,
        "hazard_type": hazard_type,
        "title": r.get("title"),
        "properties": r.get("properties") or {},
        # column is 2D (USGS points carry depth as a Z coordinate), and many NIFC
        # perimeters self-intersect, which breaks ST_DWithin on geography; repair them
        "geom": func.ST_SetSRID(func.ST_MakeValid(
            func.ST_Force2D(func.ST_GeomFromGeoJSON(json.dumps(r["geometry"])))), 4326),
        "observed_at": r.get("observed_at"),
        "fetched_at": now,
    } for source_id, r in unique.items()]

    for start in range(0, len(rows), BATCH_SIZE):
        stmt = insert(HazardFeature).values(rows[start:start + BATCH_SIZE])
        stmt = stmt.on_conflict_do_update(
            index_elements=["source", "source_id"],
            set_={c: stmt.excluded[c] for c in
                  ("hazard_type", "title", "properties", "geom", "observed_at", "fetched_at")},
        )
        db.session.execute(stmt)

    # replaces Mongo's TTL index: anything not refreshed in this run is gone from the feed.
    # Only reached after a successful fetch, so an upstream outage never empties the table.
    db.session.execute(delete(HazardFeature).where(
        HazardFeature.source == source, HazardFeature.fetched_at < now))
    db.session.commit()
    return len(rows)
