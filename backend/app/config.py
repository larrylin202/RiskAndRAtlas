import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-dev-key")
    #DATABASE_URI = os.getenv("DATABASE_URI", "mongodb://localhost:27017/rr_atlas")
    AIRNOW_API_KEY = os.getenv("AIRNOW_API_KEY")
    NOAA_USER_AGENT = os.getenv("NOAA_USER_AGENT", "(RRAtlas, dev@example.com)")
    REDIS_URL = os.getenv("REDIS_URL")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URI", "postgresql+psycopg://rr:rr@localhost:5432/rr_atlas"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,  # hosted DBs drop idle connections
        "connect_args": {"connect_timeout": 5},
    }
    # refresh hazard feeds in the background when they're older than this (services/refresh.py)
    AUTO_INGEST = os.getenv("AUTO_INGEST", "true").lower() == "true"
    INGEST_STALE_MINUTES = int(os.getenv("INGEST_STALE_MINUTES", "10"))