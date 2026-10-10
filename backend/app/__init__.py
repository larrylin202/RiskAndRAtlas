from flask import Flask
from flask_cors import CORS
from .config import Config
from .extensions import db, migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)

    @app.route("/api/health")
    def health():
        return {"status": "healthy", "service": "R&R Atlas Backend"}

    # Register the hazards blueprint we just created
    from .api.hazards import hazards_bp
    app.register_blueprint(hazards_bp, url_prefix="/api/hazards")
    
    # Register the risk scoring blueprint
    from .api.scoring import scoring_bp
    app.register_blueprint(scoring_bp, url_prefix="/api/risk")

    db.init_app(app)
    migrate.init_app(app, db)
    from . import models # so Alembic sees the tables

    @app.cli.command("ingest")
    def ingest():
        """Fetch every bulk hazard feed and upsert it into hazard_features."""
        from .services import usgs, nifc, rtfi
        for name, service in (("earthquakes", usgs), ("wildfires", nifc), ("floods", rtfi)):
            # one failing feed shouldn't stop the others
            try:
                print(f"{name}: {service.refresh()} rows")
            except Exception as e:
                db.session.rollback()
                print(f"{name}: FAILED - {e}")

    return app