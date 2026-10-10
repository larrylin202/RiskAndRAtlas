from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify
from sqlalchemy import func, select

from ..extensions import db
from ..models import HazardFeature
from ..scoring.calculator import earthquake_score, combined_risk_score

scoring_bp = Blueprint("scoring", __name__)

# Only earthquakes within this radius and age contribute to the
# preliminary location-based earthquake risk score.
EARTHQUAKE_RADIUS_KM = 50.0
EARTHQUAKE_MAX_AGE_DAYS = 30


@scoring_bp.route("/score", methods=["GET"])
def get_risk_score():
    latitude = request.args.get("lat", type=float)
    longitude = request.args.get("lon", type=float)

    if latitude is None or longitude is None:
        return jsonify({
            "error": "Both lat and lon are required"
        }), 400

    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return jsonify({
            "error": "lat must be between -90 and 90 and lon between -180 and 180"
        }), 400

    now = datetime.now(timezone.utc)

    # geography(...) makes distances meters on the spheroid; the expression
    # matches idx_hazard_features_geog so ST_DWithin can use the index.
    point = func.geography(func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326))
    geom = func.geography(HazardFeature.geom)

    nearby_earthquakes = db.session.execute(
        select(
            HazardFeature.properties["mag"].as_float(),
            HazardFeature.observed_at,
            func.ST_Distance(geom, point),
        ).where(
            HazardFeature.hazard_type == "earthquake",
            HazardFeature.observed_at >= now - timedelta(days=EARTHQUAKE_MAX_AGE_DAYS),
            func.ST_DWithin(geom, point, EARTHQUAKE_RADIUS_KM * 1000),
        )
    ).all()

    earthquake_distances = []

    for magnitude, event_time, distance_m in nearby_earthquakes:
        if magnitude is None:
            continue

        distance_km = distance_m / 1000
        age_days = (now - event_time).total_seconds() / 86400

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

    # Calculate the preliminary combined risk score.
    # Currently, earthquake is the only available component.
    combined_risk = combined_risk_score(
        earthquake=earthquake_risk
    )

    return jsonify({
        "latitude": latitude,
        "longitude": longitude,
        "earthquake_count": len(earthquake_distances),
        "earthquake_risk": earthquake_risk,
        "combined_risk": combined_risk,
        "strongest_earthquake": strongest_earthquake,
    })
