import math
import requests
from .ingest import upsert_features, from_epoch_ms

FEED_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/{feed}.geojson"


def _style(properties):
    """Inject hazardType and map circle styling into an earthquake's properties."""
    mag = properties.get("mag")
    properties["hazardType"] = "earthquake"

    radius = 500  # Default fallback radius
    fill_color = "gray"

    if mag is not None:
        # Apply McCue's formula for radius based on magnitude
        if mag > 0:
            radius_in_km = math.exp((mag / 1.01) - 0.13)
            radius = round(radius_in_km * 1000)

        # Color coordinates based on the magnitude
        if mag <= 2:
            fill_color = "green"
        elif mag <= 4.5:
            fill_color = "orange"
        else:
            fill_color = "red"

    properties["radius"] = radius
    properties["fillColor"] = fill_color
    properties["fillOpacity"] = 0.4


def fetch_earthquakes(feed="all_day"):
    """Fetch a USGS summary feed (all_hour / all_day / all_week / all_month) as styled GeoJSON features."""
    response = requests.get(FEED_URL.format(feed=feed), timeout=30)
    response.raise_for_status()

    features = response.json().get("features", [])
    for feature in features:
        properties = feature.setdefault("properties", {})
        _style(properties)
        coordinates = (feature.get("geometry") or {}).get("coordinates") or []
        if len(coordinates) > 2:
            # depth is the Z coordinate, which the 2D geom column drops
            properties["depth_km"] = coordinates[2]
    return features


def refresh():
    # all_month so the scoring recency window (0-30 days) has data to work with
    features = fetch_earthquakes("all_month")
    return upsert_features("usgs", "earthquake", [{
        "source_id": f.get("id"),
        "title": f["properties"].get("title"),
        "properties": f["properties"],
        "geometry": f.get("geometry"),
        "observed_at": from_epoch_ms(f["properties"].get("time")),
    } for f in features])
