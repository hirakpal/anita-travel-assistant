import re
import json
from typing import List
from utils.models import Alert, Event, Location, News


def _strip_code_fence(raw_text: str) -> str:
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"```\s*$", "", text)
    return text


def _extract_json_list(raw_text: str, wrapper_keys):
    """
    Gemini is asked to "return strictly in JSON format", often wrapped in a
    ```json ... ``` code fence and/or nested under a wrapper key (e.g.
    {"destination": ..., "news": [...]}). Try to pull out the actual list of
    items; return None if the text isn't JSON at all so callers can fall
    back to plain-text parsing.
    """
    text = _strip_code_fence(raw_text)

    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in wrapper_keys:
            if isinstance(data.get(key), list):
                return data[key]
        # Fall back to the first list-valued field in the object
        for value in data.values():
            if isinstance(value, list):
                return value
        return [data]
    return None


def extract_json_object(raw_text: str):
    """
    Like _extract_json_list, but for a single JSON object response (e.g.
    Anita's chat turns: {"reply": ..., "trip_info": {...}, "ready": bool}).
    Returns None if the text isn't valid JSON.
    """
    text = _strip_code_fence(raw_text)
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None
    return data if isinstance(data, dict) else None

def parse_hotels_json_output(raw_text: str) -> List[dict]:
    """
    Parse hotel_agent's Gemini response (asked to return strict JSON per
    HOTEL_PROMPT) into the flat shape main.py's Hotels tab expects:
    name, price, rating, popularity. Falls back to the raw text on failure
    so the UI still shows something instead of crashing.
    """
    items = _extract_json_list(raw_text, wrapper_keys=["hotels"])
    if items is None:
        return [{"raw_output": raw_text}]

    hotels = []
    for item in items:
        if not isinstance(item, dict):
            continue
        hotels.append({
            "name": item.get("name", "Unknown"),
            "location": item.get("location"),
            "price": item.get("price", item.get("price_range", "N/A")),
            "rating": item.get("rating", "N/A"),
            "popularity": item.get("popularity", ""),
            "fit": item.get("fit"),
            "room_type": item.get("room_type"),
            "bed_size": item.get("bed_size"),
            "style": item.get("style"),
            "amenities": item.get("amenities", []),
            "highlights": item.get("highlights"),
            "review_summary": item.get("review_summary"),
            "distances": item.get("distances", []),
        })
    return hotels or [{"raw_output": raw_text}]


def parse_food_json_output(raw_text: str) -> List[dict]:
    """Parse food_agent's Gemini response into the shape the Culinary tab expects."""
    items = _extract_json_list(raw_text, wrapper_keys=["restaurants"])
    if items is None:
        return [{"raw_output": raw_text}]

    restaurants = []
    for item in items:
        if not isinstance(item, dict):
            continue
        restaurants.append({
            "name": item.get("name", "Restaurant"),
            "cuisine": item.get("cuisine"),
            "price": item.get("price", item.get("price_range", "N/A")),
            "rating": item.get("rating", "N/A"),
            "popularity": item.get("popularity", ""),
            "distance": item.get("distance"),
            "duration": item.get("duration"),
            "fit": item.get("fit"),
            "specialties": item.get("specialties", []),
            "ambiance": item.get("ambiance"),
            "dietary_options": item.get("dietary_options", []),
            "review_summary": item.get("review_summary"),
        })
    return restaurants or [{"raw_output": raw_text}]


def parse_transport_json_output(raw_text: str) -> List[dict]:
    """Parse transport_agent's Gemini response into the shape the Transport tab expects."""
    items = _extract_json_list(raw_text, wrapper_keys=["transport_options", "transport"])
    if items is None:
        return [{"raw_output": raw_text}]

    options = []
    for item in items:
        if not isinstance(item, dict):
            continue
        options.append({
            "name": item.get("name", item.get("mode", "Transport")),
            "price": item.get("price", item.get("price_range", "N/A")),
            "rating": item.get("rating", "N/A"),
            "popularity": item.get("popularity", ""),
            "distance": item.get("distance"),
            "duration": item.get("duration"),
        })
    return options or [{"raw_output": raw_text}]


def parse_booking_output(raw_text: str):
    """
    Parse Gemini free-text booking output into structured JSON.
    Supports multiple bookings by splitting on 'Booking ID' or 'Reservation'.
    """

    bookings = []
    # Split raw text into chunks per booking
    chunks = re.split(r"(?:Booking ID|Reservation)[:\- ]", raw_text, flags=re.IGNORECASE)

    for chunk in chunks:
        if not chunk.strip():
            continue

        parsed = {
            "confirmation": None,
            "cancellation_policy": None,
            "payment_options": [],
            "reviews": {"rating": None, "highlights": []},
            "status": None
        }

        # Confirmation
        conf_match = re.search(r"([A-Z0-9]{3,})", chunk)
        if conf_match:
            parsed["confirmation"] = conf_match.group(1)

        # Cancellation policy
        cancel_match = re.search(r"(cancellation policy|cancellation)[:\- ]+(.+?)(\.|\n)", chunk, re.IGNORECASE)
        if cancel_match:
            parsed["cancellation_policy"] = cancel_match.group(2).strip()

        # Payment options
        payments = re.findall(r"(Credit Card|PayPal|Cash|UPI)", chunk, re.IGNORECASE)
        if payments:
            parsed["payment_options"] = list(set([p.title() for p in payments]))

        # Reviews
        rating_match = re.search(r"rating[:\- ]+([0-9]\.[0-9])", chunk, re.IGNORECASE)
        if rating_match:
            parsed["reviews"]["rating"] = float(rating_match.group(1))

        highlights = re.findall(r"(easy booking|refund|support|smooth|secure payment)", chunk, re.IGNORECASE)
        if highlights:
            parsed["reviews"]["highlights"] = list(set([h.capitalize() for h in highlights]))

        # Status
        if "confirmed" in chunk.lower() or "reservation" in chunk.lower():
            parsed["status"] = "Reservation confirmed"

        bookings.append(parsed)

    return bookings
import re

def parse_hotels_output(raw_text: str):
    hotels = []
    chunks = re.split(r"(?:Hotel|Property)[:\- ]", raw_text, flags=re.IGNORECASE)

    for chunk in chunks:
        if not chunk.strip():
            continue

        parsed = {
            "name": None,
            "location": None,
            "room_types": [],
            "amenities": [],
            "price_range": None,
            "reviews": {"rating": None, "highlights": []},
            "fit": None
        }

        name_match = re.search(r"([A-Za-z ]+)", chunk)
        if name_match:
            parsed["name"] = name_match.group(1).strip()

        loc_match = re.search(r"(near|location)[:\- ]+(.+?)(\.|\n)", chunk, re.IGNORECASE)
        if loc_match:
            parsed["location"] = loc_match.group(2).strip()

        rooms = re.findall(r"(Standard|Deluxe|Suite)", chunk, re.IGNORECASE)
        parsed["room_types"] = list(set([r.title() for r in rooms]))

        amenities = re.findall(r"(WiFi|Pool|Breakfast|Gym)", chunk, re.IGNORECASE)
        parsed["amenities"] = list(set([a.title() for a in amenities]))

        price_match = re.search(r"\$\d+–\$\d+", chunk)
        if price_match:
            parsed["price_range"] = price_match.group(0)

        rating_match = re.search(r"rating[:\- ]+([0-9]\.[0-9])", chunk, re.IGNORECASE)
        if rating_match:
            parsed["reviews"]["rating"] = float(rating_match.group(1))

        highlights = re.findall(r"(service|food|location|value|comfort)", chunk, re.IGNORECASE)
        parsed["reviews"]["highlights"] = list(set([h.capitalize() for h in highlights]))

        fit_match = re.search(r"(fit|best for)[:\- ]+(.+?)(\.|\n)", chunk, re.IGNORECASE)
        if fit_match:
            parsed["fit"] = fit_match.group(2).strip()

        hotels.append(parsed)
    return hotels

def parse_food_output(raw_text: str):
    restaurants = []
    chunks = re.split(r"(?:Restaurant|Eatery)[:\- ]", raw_text, flags=re.IGNORECASE)

    for chunk in chunks:
        if not chunk.strip():
            continue

        parsed = {
            "name": None,
            "cuisine": None,
            "dietary_options": [],
            "seating": None,
            "price_range": None,
            "reviews": {"rating": None, "highlights": []},
            "fit": None
        }

        name_match = re.search(r"([A-Za-z ]+)", chunk)
        if name_match:
            parsed["name"] = name_match.group(1).strip()

        cuisine_match = re.search(r"(cuisine|type)[:\- ]+(.+?)(\.|\n)", chunk, re.IGNORECASE)
        if cuisine_match:
            parsed["cuisine"] = cuisine_match.group(2).strip()

        dietary = re.findall(r"(Vegetarian|Vegan|Gluten-free)", chunk, re.IGNORECASE)
        parsed["dietary_options"] = list(set([d.title() for d in dietary]))

        seating_match = re.search(r"(seating|style)[:\- ]+(.+?)(\.|\n)", chunk, re.IGNORECASE)
        if seating_match:
            parsed["seating"] = seating_match.group(2).strip()

        price_match = re.search(r"\$\d+–\$\d+", chunk)
        if price_match:
            parsed["price_range"] = price_match.group(0)

        rating_match = re.search(r"rating[:\- ]+([0-9]\.[0-9])", chunk, re.IGNORECASE)
        if rating_match:
            parsed["reviews"]["rating"] = float(rating_match.group(1))

        highlights = re.findall(r"(authentic|friendly|quick service|atmosphere)", chunk, re.IGNORECASE)
        parsed["reviews"]["highlights"] = list(set([h.capitalize() for h in highlights]))

        fit_match = re.search(r"(fit|best for)[:\- ]+(.+?)(\.|\n)", chunk, re.IGNORECASE)
        if fit_match:
            parsed["fit"] = fit_match.group(2).strip()

        restaurants.append(parsed)

    return restaurants

def parse_transport_output(raw_text: str):
    transports = []
    chunks = re.split(r"(?:Transport|Mode)[:\- ]", raw_text, flags=re.IGNORECASE)

    for chunk in chunks:
        if not chunk.strip():
            continue

        parsed = {
            "mode": None,
            "duration": None,
            "price_range": None,
            "availability": None,
            "reviews": {"rating": None, "highlights": []},
            "fit": None
        }

        mode_match = re.search(r"(Cab|Metro|Bus|Rental Car)", chunk, re.IGNORECASE)
        if mode_match:
            parsed["mode"] = mode_match.group(1).title()

        duration_match = re.search(r"(\d+ ?min|\d+ ?hours?)", chunk)
        if duration_match:
            parsed["duration"] = duration_match.group(1)

        price_match = re.search(r"\$\d+–\$\d+", chunk)
        if price_match:
            parsed["price_range"] = price_match.group(0)

        avail_match = re.search(r"(availability)[:\- ]+(.+?)(\.|\n)", chunk, re.IGNORECASE)
        if avail_match:
            parsed["availability"] = avail_match.group(2).strip()

        rating_match = re.search(r"rating[:\- ]+([0-9]\.[0-9])", chunk, re.IGNORECASE)
        if rating_match:
            parsed["reviews"]["rating"] = float(rating_match.group(1))

        highlights = re.findall(r"(reliable|comfortable|budget|fast)", chunk, re.IGNORECASE)
        parsed["reviews"]["highlights"] = list(set([h.capitalize() for h in highlights]))

        fit_match = re.search(r"(fit|best for)[:\- ]+(.+?)(\.|\n)", chunk, re.IGNORECASE)
        if fit_match:
            parsed["fit"] = fit_match.group(2).strip()

        transports.append(parsed)

    return transports

import json

def parse_flights_output(text: str) -> list[dict]:
    """
    Parse Gemini's flight JSON output into a structured list of flights.
    Expected fields: airline, route, departure, arrival, duration,
                     class_options, baggage_allowance, price_range,
                     reviews, fit.
    """
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "flights" in data:
            flights = data["flights"]
        elif isinstance(data, list):
            flights = data
        else:
            flights = [data]

        parsed = []
        for f in flights:
            parsed.append({
                "airline": f.get("airline", "Unknown"),
                "route": f.get("route", ""),
                "departure": f.get("departure", ""),
                "arrival": f.get("arrival", ""),
                "duration": f.get("duration", ""),
                "class_options": f.get("class_options", []),
                "baggage_allowance": f.get("baggage_allowance", ""),
                "price_range": f.get("price_range", ""),
                "reviews": f.get("reviews", {}),
                "fit": f.get("fit", ""),
                "constraint_applied": f.get("constraint_applied", "none")
            })
        return parsed

    except Exception as e:
        # Fallback: return raw text if parsing fails
        return [{"raw_output": text, "error": str(e)}]


def _parse_flight_leg(items):
    parsed = []
    for f in items:
        if not isinstance(f, dict):
            continue
        parsed.append({
            "airline": f.get("airline", "Unknown"),
            "route": f.get("route", ""),
            "departure": f.get("departure", ""),
            "arrival": f.get("arrival", ""),
            "duration": f.get("duration", ""),
            "class_options": f.get("class_options", []),
            "baggage_allowance": f.get("baggage_allowance", ""),
            "price_range": f.get("price", f.get("price_range", "")),
            "rating": f.get("rating", "N/A"),
            "fit": f.get("fit", ""),
        })
    return parsed


def parse_roundtrip_flights_output(text: str) -> dict:
    """
    Parse flight_agent's Gemini response (asked to return strict JSON per
    FLIGHT_PROMPT) into {"outbound": [...], "return": [...]}. Falls back to
    the raw text under "outbound" if Gemini didn't return JSON.
    """
    outbound = _extract_json_list(text, wrapper_keys=["outbound_flights"])
    if outbound is None:
        return {"outbound": [{"raw_output": text}], "return": []}

    return_leg = _extract_json_list(text, wrapper_keys=["return_flights"]) or []
    return {
        "outbound": _parse_flight_leg(outbound) or [{"raw_output": text}],
        "return": _parse_flight_leg(return_leg),
    }


def parse_tours_output(raw_text: str) -> List[dict]:
    """
    Parse tour_agent's Gemini response (asked to return strict JSON per
    TOUR_PROMPT) into the shape main.py's Activities tab expects: title,
    location, price, rating, popularity, duration. Falls back to treating
    each paragraph as one tour if Gemini didn't return JSON.
    """
    items = _extract_json_list(raw_text, wrapper_keys=["tours"])
    if items is not None:
        tours = []
        for item in items:
            if not isinstance(item, dict):
                continue
            tours.append({
                "title": item.get("title", "Activity"),
                "location": item.get("location"),
                "price": item.get("price", item.get("price_range", "N/A")),
                "rating": item.get("rating", "N/A"),
                "popularity": item.get("popularity", "🔥 Popular"),
                "duration": item.get("duration"),
                "accessibility_notes": item.get("accessibility_notes"),
                "fit": item.get("fit"),
                "what_to_expect": item.get("what_to_expect"),
                "best_time": item.get("best_time"),
                "tips": item.get("tips"),
            })
        if tours:
            return tours

    # Fallback: not JSON, treat each paragraph as one tour
    tours = []
    for chunk in raw_text.split("\n\n"):
        if not chunk.strip():
            continue
        tours.append({
            "title": chunk.split("\n")[0],
            "description": chunk,
            "duration": None,
            "price_range": None,
            "accessibility_notes": None
        })
    return tours

def parse_alerts_output(raw_text: str) -> List[dict]:
    alerts = []

    items = _extract_json_list(raw_text, wrapper_keys=["alerts", "advisories"])
    if items is not None:
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                alert = Alert(
                    type=item.get("type", "General"),
                    message=item.get("message", ""),
                    severity=item.get("severity"),
                )
                alerts.append(alert.dict())
            except Exception as e:
                print(f"⚠️ Alert parse error: {e!r}")
        return alerts

    # Fallback: not JSON, treat each non-empty line as one alert
    for chunk in raw_text.split("\n"):
        if not chunk.strip():
            continue
        try:
            alert = Alert(type="General", message=chunk.strip(), severity=None)
            alerts.append(alert.dict())
        except Exception as e:
            print(f"⚠️ Alert parse error: {e!r}")
    return alerts

def parse_events_output(raw_text: str) -> List[dict]:
    events = []

    items = _extract_json_list(raw_text, wrapper_keys=["events"])
    if items is not None:
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                event = Event(
                    name=item.get("name", "Event"),
                    date=item.get("date"),
                    location=item.get("location"),
                    description=item.get("description"),
                    price_range=item.get("price_range"),
                    reviews=item.get("reviews"),
                )
                events.append(event.dict())
            except Exception as e:
                print(f"⚠️ Event parse error: {e!r}")
        return events

    # Fallback: not JSON, treat each paragraph as one event
    for chunk in raw_text.split("\n\n"):
        if not chunk.strip():
            continue
        try:
            event = Event(name=chunk.split("\n")[0], date=None, location=None, description=chunk)
            events.append(event.dict())
        except Exception as e:
            print(f"⚠️ Event parse error: {e!r}")
    return events

def parse_locations_output(raw_text: str) -> List[dict]:
    locations = []

    items = _extract_json_list(raw_text, wrapper_keys=["locations"])
    if items is not None:
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                location = Location(
                    name=item.get("name", "Location"),
                    type=item.get("type", "Landmark"),
                    opening_hours=item.get("opening_hours"),
                    price_range=item.get("price_range"),
                    reviews=item.get("reviews"),
                )
                locations.append(location.dict())
            except Exception as e:
                print(f"⚠️ Location parse error: {e!r}")
        return locations

    # Fallback: not JSON, treat each paragraph as one location
    for chunk in raw_text.split("\n\n"):
        if not chunk.strip():
            continue
        try:
            location = Location(name=chunk.split("\n")[0], type="Landmark", opening_hours=None, price_range=None)
            locations.append(location.dict())
        except Exception as e:
            print(f"⚠️ Location parse error: {e!r}")
    return locations

def parse_news_output(raw_text: str) -> List[dict]:
    news_items = []

    items = _extract_json_list(raw_text, wrapper_keys=["news"])
    if items is not None:
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                news = News(
                    headline=item.get("headline", "News"),
                    source=item.get("source"),
                    date=item.get("date"),
                    summary=item.get("summary"),
                )
                news_items.append(news.dict())
            except Exception as e:
                print(f"⚠️ News parse error: {e!r}")
        return news_items

    # Fallback: not JSON, treat each paragraph as one news item
    for chunk in raw_text.split("\n\n"):
        if not chunk.strip():
            continue
        try:
            news = News(headline=chunk.split("\n")[0], source=None, date=None, summary=chunk)
            news_items.append(news.dict())
        except Exception as e:
            print(f"⚠️ News parse error: {e!r}")
    return news_items


