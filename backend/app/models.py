from datetime import datetime, timezone
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSONB
from .extensions import db

class HazardFeature(db.Model):
    __tablename__ = "hazard_features"
    __table_args__ = (db.UniqueConstraint("source", "source_id"),)

    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(32), nullable=False)       # 'usgs', 'nifc', ...
    source_id = db.Column(db.String(128), nullable=False)   # feature id from the feed
    hazard_type = db.Column(db.String(32), nullable=False, index=True)
    title = db.Column(db.Text)
    properties = db.Column(JSONB, nullable=False, default=dict)  # everything else from the feed
    geom = db.Column(Geometry("GEOMETRY", srid=4326), nullable=False)  # GIST index created automatically
    observed_at = db.Column(db.DateTime(timezone=True))
    # when ingest last *wrote* this row (unchanged rows are skipped, see services/ingest.py);
    # when a feed was last checked lives in IngestRun.last_success_at
    fetched_at = db.Column(db.DateTime(timezone=True), nullable=False,
                default=lambda: datetime.now(timezone.utc), index=True)


class IngestRun(db.Model):
    """One row per feed: when it was last refreshed, and the lease that stops two
    processes (gunicorn workers, Render instances) refreshing it at the same time."""
    __tablename__ = "ingest_runs"

    source = db.Column(db.String(32), primary_key=True)     # 'usgs', 'nifc', 'rtfi'
    last_attempt_at = db.Column(db.DateTime(timezone=True)) # set when a refresh is claimed/started
    last_success_at = db.Column(db.DateTime(timezone=True))
    row_count = db.Column(db.Integer)                       # features in the feed at last success
    last_error = db.Column(db.Text)                         # None after a success