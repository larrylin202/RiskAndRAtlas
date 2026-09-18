import math
import requests
from flask import Blueprint, jsonify

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