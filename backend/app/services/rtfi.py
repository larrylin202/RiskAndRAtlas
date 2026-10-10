import requests
from .ingest import upsert_features

FLOODING_URL = "https://api.waterdata.usgs.gov/rtfi-api/referencepoints/flooding/geojson"


def _map_properties(properties):
    """Inject hazardType and build title/place from the reference point and gauge site names."""
    properties["hazardType"] = "flood"

    # Fixes property name differences between APIs; either name can be missing
    names = [properties.get("rp_name"), properties.get("site_name")]
    properties["title"] = " - ".join(n for n in names if n) or "Flooding"
    properties["place"] = properties.get("site_name")


def fetch_floods():
    """Fetch reference points that are currently flooding.

    Note: the endpoint's CloudFront blocks curl's default User-Agent; requests' default is fine.
    """
    response = requests.get(FLOODING_URL, timeout=30)
    response.raise_for_status()

    features = response.json().get("features", [])
    for feature in features:
        _map_properties(feature.setdefault("properties", {}))
    return features


def refresh():
    features = fetch_floods()
    return upsert_features("rtfi", "flood", [{
        "source_id": f["properties"].get("id") or f.get("id"),
        "title": f["properties"].get("title"),
        "properties": f["properties"],
        "geometry": f.get("geometry"),
        # the feed has no per-point timestamp
        "observed_at": None,
    } for f in features])
