import requests
from datetime import datetime, timedelta, timezone
from flask import Blueprint, Response, request, jsonify
from sqlalchemy import JSON, Text, cast, func, literal_column, select
from ..config import Config
from ..extensions import db
from ..models import HazardFeature

hazards_bp = Blueprint("hazards", __name__)

# hazard_features keeps a month of earthquakes (for scoring); the map shows the last day by default
EARTHQUAKE_DEFAULT_DAYS = 1
EARTHQUAKE_MAX_DAYS = 30


def _feature_collection(hazard_type, *criteria):
    """Return the stored features of one hazard type as a GeoJSON FeatureCollection response.

    The JSON is built in Postgres and passed through as text, so large wildfire
    polygons aren't parsed and re-serialized in Python. Feeds are refreshed in the
    background (services/refresh.py), so this never calls upstream.
    """
    feature = func.json_build_object(
        "type", "Feature",
        "id", HazardFeature.source_id,
        "properties", HazardFeature.properties,
        "geometry", cast(func.ST_AsGeoJSON(HazardFeature.geom), JSON),
    )
    collection = func.json_build_object(
        "type", "FeatureCollection",
        "features", func.coalesce(func.json_agg(feature), literal_column("'[]'::json")),
    )
    body = db.session.execute(
        select(cast(collection, Text))
        .where(HazardFeature.hazard_type == hazard_type, *criteria)
    ).scalar_one()
    return Response(body, mimetype="application/json")


@hazards_bp.route("/earthquakes", methods=["GET"])
def get_earthquakes():
    days = request.args.get("days", EARTHQUAKE_DEFAULT_DAYS, type=float)
    if not 0 < days <= EARTHQUAKE_MAX_DAYS:
        return jsonify({"error": f"days must be between 0 and {EARTHQUAKE_MAX_DAYS}"}), 400
    since = datetime.now(timezone.utc) - timedelta(days=days)
    return _feature_collection("earthquake", HazardFeature.observed_at >= since)

@hazards_bp.route("/wildfires", methods=["GET"])
def get_wildfires():
    return _feature_collection("wildfire")

@hazards_bp.route("/floods", methods=["GET"])
def get_floods():
    return _feature_collection("flood")

@hazards_bp.route("/air_quality", methods=["GET"])
def get_air_quality():
    zipcode = request.args.get('zip')
    latitude = request.args.get("lat", type=float)
    longitude = request.args.get("lon", type=float)
    api_key = Config.AIRNOW_API_KEY

    
    if longitude is not None and latitude is not None:
        url = f"https://www.airnowapi.org/aq/observation/current/ziplatlong/?format=text/csv&latitude={latitude}&longitude={longitude}&API_KEY={api_key}"
    elif zipcode is not None:
        url = f"https://www.airnowapi.org/aq/observation/current/ziplatlong/?format=text/csv&zipcode={zipcode}&API_KEY={api_key}"
    else:
            return jsonify({
                "error": "Either zip is required or both lat and lon are required"
            }), 400
    
    try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            json_data = response.json()
        
            return jsonify(json_data)
    
    except requests.RequestException as e:
        return jsonify({"error": "Failed to fetch AirNow data", "details": str(e)}), 500