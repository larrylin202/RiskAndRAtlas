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
    
    return app