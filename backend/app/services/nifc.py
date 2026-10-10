import requests
from .ingest import upsert_features, from_epoch_ms

QUERY_URL = (
    "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/"
    "WFIGS_Interagency_Perimeters_Current/FeatureServer/0/query"
)
PAGE_SIZE = 2000  # layer's maxRecordCount
MAX_PAGES = 50    # guard against a server that never clears exceededTransferLimit


def _map_properties(properties):
    """Inject hazardType and normalize NIFC attribute names to the shared title/place/size keys."""
    properties["hazardType"] = "wildfire"

    # Fixes property name differences between APIs
    properties["title"] = properties.get("attr_IncidentName") or properties.get("poly_IncidentName")
    properties["place"] = properties.get("attr_IncidentShortDescription")

    size = properties.get("attr_CalculatedAcres")
    if size is not None:
        properties["size"] = round(size)


def fetch_wildfires():
    """Fetch all current fire perimeters, following ArcGIS paging."""
    features = []
    for page in range(MAX_PAGES):
        response = requests.get(QUERY_URL, params={
            "where": "1=1",
            "outFields": "*",
            "orderByFields": "OBJECTID",
            "resultOffset": page * PAGE_SIZE,
            "resultRecordCount": PAGE_SIZE,
            "f": "geojson",
        }, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "error" in data:  # ArcGIS reports query errors with HTTP 200
            raise requests.RequestException(f"ArcGIS query error: {data['error']}")

        batch = data.get("features", [])
        features.extend(batch)
        if not batch or not (data.get("properties") or {}).get("exceededTransferLimit"):
            break

    for feature in features:
        _map_properties(feature.setdefault("properties", {}))
    return features


def refresh():
    features = fetch_wildfires()
    return upsert_features("nifc", "wildfire", [{
        # source system's polygon id; OBJECTID can change when the layer is republished
        "source_id": (f["properties"].get("poly_SourceGlobalID")
                      or f["properties"].get("GlobalID")
                      or f.get("id")),
        "title": f["properties"].get("title"),
        "properties": f["properties"],
        "geometry": f.get("geometry"),
        "observed_at": from_epoch_ms(f["properties"].get("attr_FireDiscoveryDateTime")),
    } for f in features])
