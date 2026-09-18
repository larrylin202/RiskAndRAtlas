from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)

    @app.route("/api/health")
    def health():
        return {"status": "healthy", "service": "R&R Atlas Backend"}

    # Register the hazards blueprint we just created
    from .api.hazards import hazards_bp
    app.register_blueprint(hazards_bp, url_prefix="/api/hazards")

    return app