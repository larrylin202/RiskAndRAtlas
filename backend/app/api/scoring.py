import requests
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify

from ..scoring.calculator import earthquake_score
from ..utils.geo import haversine_distance_km

scoring_bp = Blueprint("scoring", __name__)


@scoring_bp.route("/score", methods=["GET"])
def get_risk_score():
    latitude = request.args.get("lat", type=float)
    longitude = request.args.get("lon", type=float)

    if latitude is None or longitude is None:
        return jsonify({
            "error": "Both lat and lon are required"
        }), 400

    earthquake_url = (
        "https://earthquake.usgs.gov/earthquakes/feed/v1.0/"
        "summary/all_day.geojson"
    )

    try:
        response = requests.get(earthquake_url, timeout=10)
        response.raise_for_status()

        earthquake_data = response.json()

        earthquake_features = earthquake_data.get("features", [])

        earthquake_distances = []

        for feature in earthquake_features:
            geometry = feature.get("geometry", {})
            coordinates = geometry.get("coordinates", [])

            if len(coordinates) < 2:
                continue

            earthquake_longitude = coordinates[0]
            earthquake_latitude = coordinates[1]

            distance_km = haversine_distance_km(
                latitude,
                longitude,
                earthquake_latitude,
                earthquake_longitude,
            )

            properties = feature.get("properties", {})

            magnitude = properties.get("mag")
            timestamp = properties.get("time")

            if magnitude is None or timestamp is None:
                continue

            event_time = datetime.fromtimestamp(
                timestamp / 1000,
                tz=timezone.utc,
            )

            age_days = (
                datetime.now(timezone.utc) - event_time
            ).total_seconds() / 86400

            # Only earthquakes within 50 km contribute to the
            # preliminary location-based earthquake risk score.
            if distance_km > 50.0:
                continue

            score = earthquake_score(
                magnitude,
                distance_km,
                age_days,
            )

            earthquake_distances.append({
                "distance_km": round(distance_km, 2),
                "magnitude": magnitude,
                "age_days": round(age_days, 2),
                "score": score,
            })

        # Use the highest-scoring earthquake as the preliminary
        # earthquake risk contribution for this location.
        if earthquake_distances:
            strongest_earthquake = max(
                earthquake_distances,
                key=lambda earthquake: earthquake["score"]
            )
            earthquake_risk = strongest_earthquake["score"]
        else:
            strongest_earthquake = None
            earthquake_risk = 0.0

        return jsonify({
            "latitude": latitude,
            "longitude": longitude,
            "earthquake_count": len(earthquake_features),
            "earthquake_risk": earthquake_risk,
            "strongest_earthquake": strongest_earthquake,
        })

    except requests.RequestException as e:
        return jsonify({
            "error": "Failed to fetch earthquake data",
            "details": str(e)
        }), 500