import pytest
import requests

def fullerton_result():
    return {
    "place_id": 317793751,
    "licence": "Data © OpenStreetMap contributors, ODbL 1.0. http://osm.org/copyright",
    "osm_type": "relation",
    "osm_id": 2312655,
    "lat": "33.8708215",
    "lon": "-117.9294160",
    "category": "boundary",
    "type": "administrative",
    "place_rank": 16,
    "importance": 0.5561643171557556,
    "addresstype": "city",
    "name": "Fullerton",
    "display_name": "Fullerton, Orange County, California, United States",
    "boundingbox": [
      "33.8541649",
      "33.9244572",
      "-117.9854168",
      "-117.8637071"
    ]
  }

@pytest.mark.parametrize("url", [
    "/api/geocode/search",
    "/api/geocode/search?q=",
    "/api/geocode/search?q=%20%20%20",
    "/api/geocode/search?q=" + "x" * 201,
])
def test_invalid_queries_are_rejected(client, nominatim, url):
    res = client.get(url)
    assert res.status_code == 400
    assert "error" in res.get_json()
    assert nominatim.calls == []


def test_request_sends_query_and_user_agent(client, app, nominatim):
    client.get("/api/geocode/search", query_string={"q": " Milk & Honey "})

    call = nominatim.calls[0]
    assert call["params"]["q"] == "Milk & Honey"
    assert call["headers"]["User-Agent"]
    assert call["params"]["format"] == "jsonv2"
    assert call["params"]["limit"] == app.config["MAX_RESULTS"]


def test_repeated_search_is_served_from_cache(client, nominatim):
    nominatim.payload = [fullerton_result()]

    first = client.get("/api/geocode/search?q=Fullerton")
    second = client.get("/api/geocode/search?q=%20%20FulleRTOn%20")

    assert first.get_json() == second.get_json()
    assert len(nominatim.calls) == 1


def test_failures_are_not_cached(client, nominatim):
    nominatim.error = requests.Timeout("too slow")
    assert client.get("/api/geocode/search?q=Fullerton").status_code == 502

    nominatim.error = None
    nominatim.payload = [fullerton_result()]

    assert client.get("/api/geocode/search?q=Fullerton").status_code == 200

    assert len(nominatim.calls) == 2


@pytest.mark.parametrize("status, payload", [
    (503, []),
    (200, {"error": 502})
], ids=["http error", "not a list"])
def test_502_error_cases(client, nominatim, status, payload):
    nominatim.status = status
    nominatim.payload = payload
    assert client.get("/api/geocode/search?q=Fullerton").status_code == 502


def test_cache_entries_expire(client, app, nominatim, clock):
    app.config['CACHE_SECONDS'] = 60

    client.get("/api/geocode/search?q=Fullerton")
    clock.now += 61
    client.get("/api/geocode/search?q=Fullerton")

    assert len(nominatim.calls) == 2


def test_burst_of_searches_gets_429(client, nominatim, clock):
    clock.sleep_advances_time = False

    statuses = [client.get(f"/api/geocode/search?q=place{i}").status_code
                for i in range(5)]

    assert statuses == [200, 200, 200, 200, 429]
    assert clock.sleeps == [0.0, 1.0, 2.0, 3.0]
    assert len(nominatim.calls) == 4

def test_result_is_normalized(client, nominatim):
    nominatim.payload = [fullerton_result()]

    res = client.get("/api/geocode/search?q=fullerton")

    assert res.status_code == 200
    assert res.get_json() == {"results": [{
        "bounds": [[33.8541649, -117.9854168], [33.9244572, -117.8637071]],
        "id": 317793751,
        "label": "Fullerton, Orange County, California, United States",
        "lat": 33.8708215,
        "lon": -117.929416
    }]}

def test_incomplete_results_are_skipped(client, nominatim):
    bad_lat = fullerton_result()
    bad_lat["lat"] = "abc"

    plain_number = 5

    short_bounding_box = fullerton_result()
    del short_bounding_box["boundingbox"][0]
    del short_bounding_box["boundingbox"][1]

    no_id = fullerton_result()
    del no_id["place_id"]

    nominatim.payload = [bad_lat, short_bounding_box, plain_number, fullerton_result(), no_id]

    results = client.get("/api/geocode/search?q=Fullerton").get_json()["results"]

    assert [location["label"] for location in results] == ["Fullerton, Orange County, California, United States"]


def without(entry, key):
    """A copy of an entry with one key removed."""
    return {k: v for k, v in entry.items() if k != key}

@pytest.mark.parametrize("display_name", [
    {**fullerton_result(), "display_name": ''},
    {**fullerton_result(), "display_name": None},
    without(fullerton_result(), "display_name")
], ids=["empty string", "null", "missing"])
def test_label_fallback_when_missing_name(client, nominatim, display_name):
    nominatim.payload = [display_name]

    results = client.get("/api/geocode/search?q=Fullerton").get_json()["results"]

    assert results[0]["label"] == '33.8708215, -117.929416'

def test_empty_results_are_cached(client, nominatim):
    first_res = client.get("/api/geocode/search?q=FullertonnedNotreal").get_json()
    second_res = client.get("/api/geocode/search?q=FullertonnedNotreal").get_json()

    assert first_res == {"results": []}
    assert first_res == second_res
    
    assert len(nominatim.calls) == 1

def test_hit_does_not_extend_expiry(client, nominatim, clock, app):
    app.config["CACHE_SECONDS"] = 60

    client.get("/api/geocode/search?q=Fullerton")
    clock.now += 40
    client.get("/api/geocode/search?q=Fullerton")
    assert len(nominatim.calls) == 1

    clock.now += 30
    client.get("/api/geocode/search?q=Fullerton")
    assert len(nominatim.calls) == 2

def test_cache_eviction(client, nominatim, app):
    app.config["MAX_CACHE_SIZE"] = 2

    client.get("/api/geocode/search?q=Fullerton") # cache miss, adds Fullerton to cache
    client.get("/api/geocode/search?q=Placentia") # cache miss, adds Placentia to cache
    client.get("/api/geocode/search?q=Anaheim")   # cache miss, cache is full, evict Fullerton, adds Anaheim
    client.get("/api/geocode/search?q=Fullerton") # cache miss, Fullerton was evicted, cache is full, evict Placentia, adds Fullerton

    assert len(nominatim.calls) == 4

def test_cache_move_to_end(client, nominatim, app):
    app.config["MAX_CACHE_SIZE"] = 2

    client.get("/api/geocode/search?q=Fullerton") # miss, add Fullerton, 1 call
    client.get("/api/geocode/search?q=Placentia") # miss, add Placentia, 2 calls

    client.get("/api/geocode/search?q=Fullerton") # hit, moves Fullerton to end, 2 calls

    assert len(nominatim.calls) == 2

    client.get("/api/geocode/search?q=Anaheim") # miss, removes Placentia, adds Anaheim, 3 calls
    client.get("/api/geocode/search?q=Fullerton") # hit, moves Fullerton to end, 3 calls

    assert len(nominatim.calls) == 3

    client.get("/api/geocode/search?q=Placentia") # miss, removes Anaheim, adds Placentia, 4 calls

    assert len(nominatim.calls) == 4

