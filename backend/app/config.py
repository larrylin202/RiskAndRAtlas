import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-dev-key")
    DATABASE_URI = os.getenv("DATABASE_URI", "mongodb://localhost:27017/rr_atlas")
    AIRNOW_API_KEY = os.getenv("AIRNOW_API_KEY")
    NOAA_USER_AGENT = os.getenv("NOAA_USER_AGENT", "(RRAtlas, dev@example.com)")
    REDIS_URL = os.getenv("REDIS_URL")