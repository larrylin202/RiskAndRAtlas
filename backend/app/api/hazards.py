import requests
from flask import Blueprint, request, jsonify
from ..config import Config
from ..services import usgs, nifc, rtfi

hazards_bp = Blueprint("hazards", __name__)

@hazards_bp.route("/earthquakes", methods=["GET"])
def get_earthquakes():
    try:
        features = usgs.fetch_earthquakes("all_day")
        return jsonify({"type": "FeatureCollection", "features": features})

    except requests.RequestException as e:
        return jsonify({"error": "Failed to fetch USGS data", "details": str(e)}), 500

@hazards_bp.route("/wildfires", methods=["GET"])
def get_wildfires():
    try:
        features = nifc.fetch_wildfires()
        return jsonify({"type": "FeatureCollection", "features": features})

    except requests.RequestException as e:
        return jsonify({"error": "Failed to fetch NIFC data", "details": str(e)}), 500

@hazards_bp.route("/floods", methods=["GET"])
def get_floods():
    try:
        features = rtfi.fetch_floods()
        return jsonify({"type": "FeatureCollection", "features": features})

    except requests.RequestException as e:
        return jsonify({"error": "Failed to fetch USGS data", "details": str(e)}), 500

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