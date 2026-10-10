import json
from datetime import datetime, timezone
from sqlalchemy import String, all_, bindparam, delete, func, tuple_
from sqlalchemy.dialects.postgresql import ARRAY, insert
from ..extensions import db
from ..models import HazardFeature

# Postgres caps a statement at 65,535 bind parameters; ~7 per row
BATCH_SIZE = 1000

# columns compared to decide whether a row actually changed
CONTENT_COLUMNS = ("hazard_type", "title", "properties", "geom", "observed_at")


def from_epoch_ms(value):
    """Convert an epoch-milliseconds timestamp (USGS, ArcGIS) to an aware datetime."""
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc)


def upsert_features(source, hazard_type, records):
    """Insert or update one feed's features, then delete rows the feed no longer returns.

    Each record is a dict with keys: source_id, title, properties, geometry
    (a GeoJSON geometry dict) and observed_at (datetime or None).
    Returns (seen, changed): features in the feed, and rows actually inserted or updated.
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

    changed = 0
    for start in range(0, len(rows), BATCH_SIZE):
        stmt = insert(HazardFeature).values(rows[start:start + BATCH_SIZE])
        stmt = stmt.on_conflict_do_update(
            index_elements=["source", "source_id"],
            set_={c: stmt.excluded[c] for c in CONTENT_COLUMNS + ("fetched_at",)},
            # every UPDATE leaves a dead row version behind, so leave identical rows alone
            where=tuple_(*(HazardFeature.__table__.c[c] for c in CONTENT_COLUMNS))
                .is_distinct_from(tuple_(*(stmt.excluded[c] for c in CONTENT_COLUMNS))),
        )
        # SQLAlchemy only reports rowcount for INSERT when asked to
        changed += db.session.execute(stmt.execution_options(preserve_rowcount=True)).rowcount

    # replaces Mongo's TTL index: anything this source no longer returns is gone.
    # Only reached after a successful fetch, so an upstream outage never empties the table.
    # (fetched_at can't be used for this: unchanged rows keep their old fetched_at)
    db.session.execute(delete(HazardFeature).where(
        HazardFeature.source == source,
        HazardFeature.source_id != all_(bindparam("seen_ids", list(unique), type_=ARRAY(String))),
    ))
    db.session.commit()
    return len(rows), changed
