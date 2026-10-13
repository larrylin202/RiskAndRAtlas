from flask import current_app
import threading
import time

_search_cache = {}
_cache_lock = threading.Lock()

_next_call_at = 0.0
_rate_lock = threading.Lock()

def cache_key(location_name):
    return " ".join(location_name.lower().split())

def get_cached(key):
    with _cache_lock:
        entry = _search_cache.get(key)
        if entry is None:
            current_app.logger.info(f'Cache miss.')
            return None
        expires_at, results = entry
        if time.monotonic() > expires_at:
            current_app.logger.info(f'Cache entry expired. Deleting')
            del _search_cache[key]
            return None
        current_app.logger.info(f'Cache hit.')

        # since this cache was actually used,
        # delete and add the entry back to the cache 
        # so that it doesn't delete popular entries.
        del _search_cache[key]
        _search_cache[key] = (expires_at, results)

        return results

def store_cached(key, results):
    with _cache_lock:
        if len(_search_cache) >= current_app.config["MAX_CACHE_SIZE"] and _search_cache.get(key) == None:
            del _search_cache[next(iter(_search_cache))]
        _search_cache[key] = (time.monotonic() + current_app.config["CACHE_SECONDS"], results)

def reserve_call_slot():
    """Seconds to wait before calling Nominatim, or None if wait is too long."""
    global _next_call_at
    with _rate_lock:
        now = time.monotonic()
        slot = max(now, _next_call_at)
        wait = slot - now
        if wait > current_app.config["MAX_WAIT_SECONDS"]:
            return None
        _next_call_at = slot + current_app.config["MIN_SECONDS_BETWEEN_CALLS"]
        return wait