import sys
import click
from flask import Flask, request
from sqlalchemy.exc import SQLAlchemyError
from flask_cors import CORS
from .config import Config
from .extensions import db, migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)

    @app.before_request
    def refresh_stale_feeds():
        # background refresh of stale hazard feeds; never blocks the request
        if request.path.startswith("/api/"):
            from .services.refresh import maybe_refresh_async
            maybe_refresh_async()

    @app.errorhandler(SQLAlchemyError)
    def database_error(e):
        # hazard routes read from the DB; don't leak connection details to the client
        db.session.rollback()
        app.logger.exception("database error")
        return {"error": "Database unavailable"}, 503

    @app.route("/api/health")
    def health():
        # queries the DB so an external keep-alive ping also keeps a hosted DB from pausing
        from .services.refresh import feed_status
        try:
            feeds = feed_status()
        except SQLAlchemyError:
            db.session.rollback()
            return {"status": "unhealthy", "service": "R&R Atlas Backend", "database": "unreachable"}, 503
        return {"status": "healthy", "service": "R&R Atlas Backend", "database": "ok", "feeds": feeds}

    if not app.config["NOMINATIM_USER_AGENT"]:
        raise RuntimeError("Set NOMINATIM_USER_AGENT in backend/.env")


    from .api.geocode import geocode_bp
    app.register_blueprint(geocode_bp, url_prefix="/api/geocode")
    
    from .api.hazards import hazards_bp
    app.register_blueprint(hazards_bp, url_prefix="/api/hazards")
    
    # Register the risk scoring blueprint
    from .api.scoring import scoring_bp
    app.register_blueprint(scoring_bp, url_prefix="/api/risk")

    db.init_app(app)
    migrate.init_app(app, db)
    from . import models # so Alembic sees the tables

    @app.cli.command("ingest")
    @click.argument("sources", nargs=-1)
    def ingest(sources):
        """Refresh hazard feeds now, ignoring staleness. SOURCES: usgs nifc rtfi (default: all)."""
        from .services.refresh import SERVICES, run_source
        unknown = set(sources) - set(SERVICES)
        if unknown:
            raise click.BadParameter(f"unknown source(s) {', '.join(sorted(unknown))}; choose from {', '.join(SERVICES)}")
        failed = False
        for source in sources or SERVICES:
            # one failing feed shouldn't stop the others
            try:
                seen, changed = run_source(source)
                print(f"{source}: {seen} features, {changed} inserted/updated")
            except Exception as e:
                failed = True
                print(f"{source}: FAILED - {e}")
        if failed:
            sys.exit(1)  # non-zero so a cron job reports the failure

    return app