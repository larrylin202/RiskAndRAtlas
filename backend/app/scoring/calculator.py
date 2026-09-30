def normalize(value: float, minimum: float, maximum: float) -> float:
    """
    Convert a value into a 0–100 scale.

    Values at or below minimum become 0.
    Values at or above maximum become 100.
    """

    if maximum <= minimum:
        raise ValueError("maximum must be greater than minimum")

    normalized = (value - minimum) / (maximum - minimum)

    # Keep the result between 0 and 100.
    normalized = max(0.0, min(1.0, normalized))

    return normalized * 100

def distance_score(distance_km: float, maximum_distance_km: float) -> float:
    """
    Convert distance from a hazard into a 0–100 risk contribution.

    0 km = 100 risk
    maximum distance or farther = 0 risk
    """

    if maximum_distance_km <= 0:
        raise ValueError("maximum_distance_km must be greater than 0")

    score = 1 - (distance_km / maximum_distance_km)

    # Keep the result between 0 and 1 before converting to 0–100.
    score = max(0.0, min(1.0, score))

    return score * 100

def recency_score(age_days: float, maximum_age_days: float) -> float:
    """
    Convert the age of a hazard event into a 0–100 risk contribution.

    0 days old = 100 risk
    maximum age or older = 0 risk
    """

    if maximum_age_days <= 0:
        raise ValueError("maximum_age_days must be greater than 0")

    score = 1 - (age_days / maximum_age_days)

    # Keep the result between 0 and 1.
    score = max(0.0, min(1.0, score))

    return score * 100

def earthquake_score(
    magnitude: float,
    distance_km: float,
    age_days: float,
) -> float:
    """
    Calculate a preliminary 0–100 earthquake risk contribution.

    This is a preliminary project formula and is expected to be
    adjusted as the team develops the final scoring methodology.
    """

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
    size_acres: float,
    distance_km: float,
    age_days: float,
) -> float:
    """
    Calculate a preliminary 0–100 wildfire risk contribution.

    This is a preliminary project formula and is expected to be
    adjusted as the team develops the final scoring methodology.
    """

    size_score = normalize(size_acres, 0.0, 10000.0)
    distance_component = distance_score(distance_km, 50.0)
    recency_component = recency_score(age_days, 30.0)

    score = (
        size_score * 0.5
        + distance_component * 0.3
        + recency_component * 0.2
    )

    return round(score, 2)

def combined_risk_score(
    earthquake: float,
    wildfire: float,
) -> float:
    """
    Calculate the preliminary combined environmental risk score.

    Currently averages the available earthquake and wildfire
    contributions equally. Additional hazards can be added later.
    """

    score = (earthquake + wildfire) / 2

    return round(score, 2)