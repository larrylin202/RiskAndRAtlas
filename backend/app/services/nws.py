import requests
from datetime import datetime
from ..config import Config
from .ingest import upsert_features


NWS_ALERTS_URL = "https://api.weather.gov/alerts/active"

FLOOD_EVENTS = [
    "Flood Watch",
    "Flood Warning",
    "Flash Flood Watch",
    "Flash Flood Warning",
    "Flood Advisory",
    "Areal Flood Warning",
    "Coastal Flood Watch",
    "Coastal Flood Warning",
    "Coastal Flood Advisory",
    "Lakeshore Flood Watch",
    "Lakeshore Flood Warning",
    "Lakeshore Flood Advisory",
    "River Flood Warning",
]


def parse_datetime(value):
    """Convert an NWS ISO timestamp into a Python datetime."""
    if not value:
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def fetch_alerts():
    """Fetch active NWS alerts and keep flood-related events."""

    headers = {
        "User-Agent": Config.NOAA_USER_AGENT,
        "Accept": "application/geo+json",
    }

    response = requests.get(
        NWS_ALERTS_URL,
        headers=headers,
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            f"NWS API error {response.status_code}: {response.text[:1000]}"
        )

    features = response.json().get("features", [])

    results = {}

    for feature in features:
        properties = feature.get("properties") or {}

        event = properties.get("event")
        source_id = properties.get("id") or feature.get("id")
        geometry = feature.get("geometry")

        if event not in FLOOD_EVENTS:
            continue

        if not source_id or not geometry:
            continue

        results[str(source_id)] = {
            "source_id": str(source_id),
            "title": properties.get("headline") or event,
            "properties": properties,
            "geometry": geometry,
            "observed_at": parse_datetime(
                properties.get("effective")
            ),
        }

    return list(results.values())


def refresh():
    """Fetch and store active NWS flood alerts."""
    features = fetch_alerts()

    return upsert_features(
        "nws",
        "flood_alert",
        features,
    )