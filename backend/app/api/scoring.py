import requests
from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, jsonify
from sqlalchemy import func, select

from ..config import Config
from ..extensions import db
from ..models import HazardFeature
from ..scoring.calculator import (
    earthquake_score,
    wildfire_score,
    flood_score,
    nws_alert_score,
    combined_risk_score,
)

scoring_bp = Blueprint("scoring", __name__)

EARTHQUAKE_RADIUS_KM = 50.0
EARTHQUAKE_MAX_AGE_DAYS = 30

WILDFIRE_RADIUS_KM = 50.0
FLOOD_RADIUS_KM = 50.0


def get_air_quality(latitude, longitude):
    """Fetch current AirNow observations and calculate an AQI risk score."""

    api_key = Config.AIRNOW_API_KEY

    if not api_key:
        return None

    url = "https://www.airnowapi.org/aq/observation/current/ziplatlong/"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "format": "application/json",
        "API_KEY": api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        observations = response.json()

        if not isinstance(observations, list):
            return None

        valid_observations = []

        for observation in observations:
            try:
                aqi = float(observation["nowcastAQI"])
            except (KeyError, TypeError, ValueError):
                continue

            if not 0 <= aqi <= 500:
                continue

            valid_observations.append({
                "aqi": aqi,
                "pollutant": observation.get("parameterName"),
                "category": observation.get("aqiCategoryName"),
                "date_observed": observation.get("dateObserved"),
                "hour_observed": observation.get("hourObserved"),
                "timezone": observation.get("localTimeZone"),
                "site_name": observation.get("siteName"),
                "reporting_area": observation.get("reportingAreaName"),
            })

        if not valid_observations:
            return None

        # Use the highest AQI across the available pollutants.
        worst_observation = max(
            valid_observations,
            key=lambda item: item["aqi"]
        )

        aqi = worst_observation["aqi"]

        # Convert the official 0-500 AQI scale to a preliminary 0-100 score.
        risk_score = round((aqi / 500.0) * 100, 2)

        return {
            **worst_observation,
            "risk_score": risk_score,
        }

    except (requests.RequestException, ValueError):
        # AirNow failures should not prevent other risk scores from loading.
        return None


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

    # Create the selected location as a geography point.
    point = func.geography(
        func.ST_SetSRID(
            func.ST_MakePoint(longitude, latitude),
            4326
        )
    )

    geom = func.geography(HazardFeature.geom)

    # earthquake score

    nearby_earthquakes = db.session.execute(
        select(
            HazardFeature.properties["mag"].as_float(),
            HazardFeature.observed_at,
            func.ST_Distance(geom, point),
        ).where(
            HazardFeature.hazard_type == "earthquake",
            HazardFeature.observed_at >= now - timedelta(
                days=EARTHQUAKE_MAX_AGE_DAYS
            ),
            func.ST_DWithin(
                geom,
                point,
                EARTHQUAKE_RADIUS_KM * 1000
            ),
        )
    ).all()

    earthquake_distances = []

    for magnitude, event_time, distance_m in nearby_earthquakes:

        if magnitude is None or event_time is None:
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

    if earthquake_distances:
        strongest_earthquake = max(
            earthquake_distances,
            key=lambda item: item["score"]
        )
        earthquake_risk = strongest_earthquake["score"]
    else:
        strongest_earthquake = None
        earthquake_risk = 0.0

    # wildfire score

    nearby_fires = db.session.execute(
        select(
            HazardFeature.properties,
            func.ST_Distance(geom, point),
        ).where(
            HazardFeature.hazard_type == "wildfire",
            func.ST_DWithin(
                geom,
                point,
                WILDFIRE_RADIUS_KM * 1000
            ),
        )
    ).all()

    wildfire_results = []

    for properties, distance_m in nearby_fires:

        distance_km = distance_m / 1000

        size_acres = properties.get("size")

        if size_acres is None:
            size_acres = properties.get("attr_CalculatedAcres")

        try:
            if size_acres is not None:
                size_acres = float(size_acres)
        except (TypeError, ValueError):
            size_acres = None

        score = wildfire_score(
            size_acres,
            distance_km,
        )

        wildfire_results.append({
            "title": properties.get("title"),
            "size_acres": size_acres,
            "distance_km": round(distance_km, 2),
            "score": score,
        })

    if wildfire_results:
        strongest_wildfire = max(
            wildfire_results,
            key=lambda item: item["score"]
        )
        wildfire_risk = strongest_wildfire["score"]
    else:
        strongest_wildfire = None
        wildfire_risk = 0.0

    # flood score

    nearby_floods = db.session.execute(
        select(
            HazardFeature.properties,
            func.ST_Distance(geom, point),
        ).where(
            HazardFeature.hazard_type == "flood",
            func.ST_DWithin(
                geom,
                point,
                FLOOD_RADIUS_KM * 1000
            ),
        )
    ).all()

    # Multiple reference points can share one gauge.
    # Keep only the nearest reference point per gauge.
    unique_flood_gauges = {}

    for properties, distance_m in nearby_floods:

        if properties.get("active") is not True:
            continue

        if properties.get("is_flooding") is not True:
            continue

        distance_km = distance_m / 1000

        gauge_id = (
            properties.get("nwis_id")
            or properties.get("nws_id")
            or properties.get("rp_id")
            or properties.get("title")
        )

        if gauge_id is None:
            continue

        if (
            gauge_id not in unique_flood_gauges
            or distance_km < unique_flood_gauges[gauge_id]["distance_km"]
        ):
            unique_flood_gauges[gauge_id] = {
                "gauge_id": gauge_id,
                "title": properties.get("title"),
                "distance_km": round(distance_km, 2),
            }

    flood_results = []

    for gauge in unique_flood_gauges.values():

        score = flood_score(gauge["distance_km"])

        flood_results.append({
            **gauge,
            "score": score,
        })

    if flood_results:
        nearest_flood_gauge = max(
            flood_results,
            key=lambda item: item["score"]
        )
        flood_risk = nearest_flood_gauge["score"]
    else:
        nearest_flood_gauge = None
        flood_risk = 0.0

    # NWS flood alert score

    nearby_alerts = db.session.execute(
        select(
            HazardFeature.properties,
            func.ST_Contains(
                HazardFeature.geom,
                func.ST_SetSRID(
                    func.ST_MakePoint(longitude, latitude),
                    4326
                )
            ),
        ).where(
            HazardFeature.hazard_type == "flood_alert",
        )
    ).all()

    active_alert_results = []

    for properties, contains_location in nearby_alerts:

        if not contains_location:
            continue

        expires = properties.get("expires")

        if expires:
            try:
                expires_at = datetime.fromisoformat(
                    expires.replace("Z", "+00:00")
                )

                if expires_at <= now:
                    continue

            except (ValueError, AttributeError):
                continue

        severity = properties.get("severity") or "Unknown"
        urgency = properties.get("urgency") or "Unknown"
        certainty = properties.get("certainty") or "Unknown"

        score = nws_alert_score(
            severity,
            urgency,
            certainty,
        )

        active_alert_results.append({
            "headline": properties.get("headline"),
            "event": properties.get("event"),
            "severity": severity,
            "urgency": urgency,
            "certainty": certainty,
            "score": score,
        })

    if active_alert_results:
        strongest_flood_alert = max(
            active_alert_results,
            key=lambda item: item["score"]
        )
        nws_flood_risk = strongest_flood_alert["score"]
    else:
        strongest_flood_alert = None
        nws_flood_risk = 0.0

    # Air quality score

    air_quality = get_air_quality(latitude, longitude)

    if air_quality:
        air_quality_risk = air_quality["risk_score"]
    else:
        air_quality_risk = None

    # combined risk score

    combined_risk = combined_risk_score(
        earthquake=earthquake_risk,
        wildfire=wildfire_risk,
        flood=max(flood_risk, nws_flood_risk),
        air_quality=air_quality_risk,
    )

    return jsonify({
        "latitude": latitude,
        "longitude": longitude,

        "earthquake_count": len(earthquake_distances),
        "earthquake_risk": earthquake_risk,
        "strongest_earthquake": strongest_earthquake,

        "wildfire_count": len(wildfire_results),
        "wildfire_risk": wildfire_risk,
        "strongest_wildfire": strongest_wildfire,

        "flood_gauge_count": len(flood_results),
        "flood_risk": flood_risk,
        "nearest_flood_gauge": nearest_flood_gauge,

        "nws_alert_count": len(active_alert_results),
        "nws_flood_risk": nws_flood_risk,
        "strongest_flood_alert": strongest_flood_alert,

        "air_quality_available": air_quality is not None,
        "air_quality_risk": air_quality_risk,
        "air_quality_aqi": air_quality["aqi"] if air_quality else None,
        "air_quality_category": air_quality["category"] if air_quality else None,
        "air_quality_pollutant": air_quality["pollutant"] if air_quality else None,
        "air_quality_observed_at": (
            f'{air_quality["date_observed"]} '
            f'{air_quality["hour_observed"]} '
            f'{air_quality["timezone"]}'
        ) if air_quality else None,
        "air_quality_site": air_quality["site_name"] if air_quality else None,
        "air_quality_reporting_area": (
            air_quality["reporting_area"] if air_quality else None
        ),

        "combined_risk": combined_risk,
    })
