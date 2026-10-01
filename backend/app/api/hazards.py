import math
import requests
from flask import Blueprint, request, jsonify
from ..config import Config

hazards_bp = Blueprint("hazards", __name__)

@hazards_bp.route("/earthquakes", methods=["GET"])
def get_earthquakes():
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        geojson_data = response.json()
        
        # Parse features and apply circle styling math from mapping.py
        for feature in geojson_data.get("features", []):
            properties = feature.get("properties", {})
            mag = properties.get("mag")

            # Inject the hazard type into the GeoJSON properties
            feature["properties"]["hazardType"] = 'earthquake' 
            
            radius = 500 # Default fallback radius
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
                
            # Inject the styling variables directly into the GeoJSON properties
            feature["properties"]["radius"] = radius
            feature["properties"]["fillColor"] = fill_color
            feature["properties"]["fillOpacity"] = 0.4
            
        return jsonify(geojson_data)
        
    except requests.RequestException as e:
        return jsonify({"error": "Failed to fetch USGS data", "details": str(e)}), 500

@hazards_bp.route("/wildfires", methods=["GET"])
def get_wildfires():
    url = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Interagency_Perimeters_Current/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        geojson_data = response.json()

        for feature in geojson_data.get("features", []):
            # Inject the hazard type into the GeoJSON properties
            feature["properties"]["hazardType"] = 'wildfire'

            # Fixes property name differences between APIs
            feature["properties"]["title"] = feature["properties"]["attr_IncidentName"]
            feature["properties"]["place"] = feature["properties"]["attr_IncidentShortDescription"]

            size = feature["properties"]["attr_CalculatedAcres"]
            if size != None:
                feature["properties"]["size"] = round(size)

        return jsonify(geojson_data)

    except requests.RequestException as e:
        return jsonify({"error": "Failed to fetch NIFC data", "details": str(e)}), 500

@hazards_bp.route("/floods", methods=["GET"])
def get_floods():
    url = "https://api.waterdata.usgs.gov/rtfi-api/referencepoints/flooding/geojson"

    try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
    
            geojson_data = response.json()

            for feature in geojson_data.get("features", []):
                        # Inject the hazard type into the GeoJSON properties
                        feature["properties"]["hazardType"] = 'flood'
            
                        # Fixes property name differences between APIs
                        feature["properties"]["title"] = feature["properties"]["rp_name"] + " - " + feature["properties"]["site_name"]
                        feature["properties"]["place"] = feature["properties"]["site_name"]
    
            return jsonify(geojson_data)
    
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