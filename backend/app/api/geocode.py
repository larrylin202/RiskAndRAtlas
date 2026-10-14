from flask import Blueprint, current_app, jsonify, request
import requests
import time
from ..services.search_cache import (
    cache_key, 
    get_cached, 
    reserve_call_slot, 
    store_cached
)

geocode_bp = Blueprint("geocode", __name__)

def error(message, status):
    return jsonify({"error": message}), status

@geocode_bp.route("/search", methods=["GET"])
def get_search_results():
    query = request.args.get("q", "").strip()
    if not query:
        return error("Query parameter 'q' is required.", 400)
    if len(query) > current_app.config["MAX_QUERY_LENGTH"]:
        return error(f"Query must be at most {current_app.config['MAX_QUERY_LENGTH']} characters.", 400)

    key = cache_key(query)
    cached = get_cached(key)
    if cached is not None:
        return jsonify({"results": cached})

    wait = reserve_call_slot()
    if wait is None:
        return error("Too many searches right now. Try again in a moment.", 429)
    time.sleep(wait)

    try:
        response = requests.get(
            f"{current_app.config['NOMINATIM_BASE_URL']}/search",
            params={
                "q": query,
                "limit": current_app.config["MAX_RESULTS"],
                "format": "jsonv2"
            },
            headers={"User-Agent": current_app.config["NOMINATIM_USER_AGENT"]},
            timeout=float(current_app.config["NOMINATIM_TIMEOUT"]),
        )
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list):
            current_app.logger.error("Map data is not a list")
            return error("Map search is unavailable right now.", 502)

    except (requests.RequestException, ValueError):
        current_app.logger.exception("Nominatim request failed")
        return error("Map search is unavailable right now.", 502)

    results = []
    for location in data:
        try:
            min_bounds = [float(location["boundingbox"][0]), float(location["boundingbox"][2])]
            max_bounds = [float(location["boundingbox"][1]), float(location["boundingbox"][3])]
            lat = float(location["lat"])
            lon = float(location["lon"])

            results.append({
                "id": location["place_id"],
                "lat": lat,
                "lon": lon,
                "label": location.get("display_name") or f'{lat}, {lon}',
                "bounds": [min_bounds, max_bounds]
            })
        except (ValueError, TypeError, IndexError, KeyError):
            continue

    store_cached(key, results)
    return jsonify({"results": results})