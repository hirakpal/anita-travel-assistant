# utils/google_places.py
"""
Best-effort Google Places lookup for real guest reviews of a specific
named place (e.g. a hotel), used to ground the "What travelers say"
section in actual Google reviews rather than generic destination-level
YouTube snippets.

Every call degrades to an empty list on any failure (missing key, place
not found, quota, etc.) — this must never be the reason a hotel card
fails to render.
"""
import os
import time

import requests

from utils.audit_trail import log_network

FIND_PLACE_URL = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"


def get_place_reviews(name, location_hint=None, max_reviews=5):
    """
    name:          place name, e.g. a hotel's name
    location_hint: extra context to disambiguate the search (e.g. destination city)
    Returns a list of review text strings (up to max_reviews), or [] if
    nothing could be found/fetched.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key or not name:
        return []

    query = f"{name}, {location_hint}" if location_hint else name
    request = {"query": query}
    start = time.time()
    try:
        find_resp = requests.get(FIND_PLACE_URL, params={
            "input": query, "inputtype": "textquery", "fields": "place_id", "key": api_key,
        }, timeout=10)
        find_resp.raise_for_status()
        candidates = find_resp.json().get("candidates", [])
        if not candidates:
            log_network("google_places:find_place", request, response={"candidates": 0},
                        duration_ms=(time.time() - start) * 1000)
            return []
        place_id = candidates[0]["place_id"]

        details_resp = requests.get(PLACE_DETAILS_URL, params={
            "place_id": place_id, "fields": "name,rating,reviews", "key": api_key,
        }, timeout=10)
        details_resp.raise_for_status()
        result = details_resp.json().get("result", {})
        reviews = [r.get("text", "").strip() for r in result.get("reviews", []) if r.get("text")]
        reviews = reviews[:max_reviews]

        log_network("google_places:place_details", request,
                    response={"place": result.get("name"), "reviews_found": len(reviews)},
                    duration_ms=(time.time() - start) * 1000)
        return reviews
    except Exception as e:
        log_network("google_places", request, error=e, duration_ms=(time.time() - start) * 1000)
        return []
