def normalize(value: float, minimum: float, maximum: float) -> float:
    """Convert a value into a 0–100 scale."""

    if maximum <= minimum:
        raise ValueError("maximum must be greater than minimum")

    normalized = (value - minimum) / (maximum - minimum)
    normalized = max(0.0, min(1.0, normalized))

    return normalized * 100


def distance_score(distance_km: float, maximum_distance_km: float) -> float:
    """
    0 km = 100 risk
    Maximum distance or farther = 0 risk
    """

    if maximum_distance_km <= 0:
        raise ValueError("maximum_distance_km must be greater than 0")

    score = 1 - (distance_km / maximum_distance_km)
    score = max(0.0, min(1.0, score))

    return score * 100


def recency_score(age_days: float, maximum_age_days: float) -> float:
    """Convert the age of an event into a 0–100 contribution."""

    if maximum_age_days <= 0:
        raise ValueError("maximum_age_days must be greater than 0")

    score = 1 - (age_days / maximum_age_days)
    score = max(0.0, min(1.0, score))

    return score * 100


def earthquake_score(
    magnitude: float,
    distance_km: float,
    age_days: float,
) -> float:
    """Calculate a preliminary earthquake risk score."""

    magnitude_score = normalize(magnitude, 0.0, 6.0)
    distance_component = distance_score(distance_km, 50.0)
    recency_component = recency_score(age_days, 30.0)

    score = (
        magnitude_score * 0.5
        + distance_component * 0.3
        + recency_component * 0.2
    )

    return round(score, 2)


def wildfire_score(
    size_acres: float | None,
    distance_km: float,
) -> float:
    """
    Calculate a preliminary wildfire risk score.

    If acreage is available:
        50% fire size + 50% distance

    If acreage is missing:
        100% distance
    """

    distance_component = distance_score(distance_km, 50.0)

    if size_acres is None:
        return round(distance_component, 2)

    size_component = normalize(size_acres, 0.0, 10000.0)

    score = (
        size_component * 0.5
        + distance_component * 0.5
    )

    return round(score, 2)


def flood_score(distance_km: float) -> float:
    """
    Calculate a preliminary flood risk score.

    Active flooding gauges closer to the selected location
    contribute a higher score.
    """

    return round(distance_score(distance_km, 50.0), 2)


def combined_risk_score(
    earthquake: float | None = None,
    wildfire: float | None = None,
    flood: float | None = None,
    air_quality: float | None = None,
    hospital_readiness: float | None = None,
    shelter_readiness: float | None = None,
    fire_station_readiness: float | None = None,
) -> float:
    """Average the available risk and resilience components."""

    components = [
        earthquake,
        wildfire,
        flood,
        air_quality,
        hospital_readiness,
        shelter_readiness,
        fire_station_readiness,
    ]

    available_components = [
        component for component in components
        if component is not None
    ]

    if not available_components:
        return 0.0

    score = sum(available_components) / len(available_components)

    return round(score, 2)

def nws_alert_score(severity, urgency, certainty):
    """Calculate a provisional risk score for an NWS flood alert."""

    severity_scores = {
        "Extreme": 100,
        "Severe": 85,
        "Moderate": 65,
        "Minor": 40,
        "Unknown": 0,
    }

    urgency_scores = {
        "Immediate": 100,
        "Expected": 80,
        "Future": 50,
        "Past": 0,
        "Unknown": 0,
    }

    certainty_scores = {
        "Observed": 100,
        "Likely": 85,
        "Possible": 60,
        "Unlikely": 25,
        "Unknown": 0,
    }

    severity_score = severity_scores.get(severity, 0)
    urgency_score = urgency_scores.get(urgency, 0)
    certainty_score = certainty_scores.get(certainty, 0)

    return round(
        severity_score * 0.50
        + urgency_score * 0.30
        + certainty_score * 0.20,
        2,
    )