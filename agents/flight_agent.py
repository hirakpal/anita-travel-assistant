#agents/flight_agent.py
import os
import requests
from rag.youtube_rag import query_videos, summarize_results
from prompts.flight_prompt import FLIGHT_PROMPT
from utils.parsers import parse_roundtrip_flights_output
from utils.cache import call_api
from utils.prompt_cache import build_gemini_request

# Helper functions (can be moved to utils.py)
CITY_TO_IATA = {
    "Mumbai": "BOM",
    "Bengaluru": "BLR",
    "Tokyo": "HND",
    "Singapore": "SIN",
    "New York": "JFK"
}

def _city_to_iata(city: str) -> str:
    if not city:
        return ""
    return CITY_TO_IATA.get(city.strip(), city.strip().upper()[:3])

def _google_flights_url(origin: str, dest: str, start: str | None, end: str | None) -> str:
    from urllib.parse import quote_plus
    q = f"Flights from {origin} to {dest}"
    if start:
        q += f" on {start}"
    return f"https://www.google.com/travel/flights?q={quote_plus(q)}"

def _is_passenger_airline(name: str) -> bool:
    banned = ["cargo","freight","logistics","courier","express","blue dart","fedex","ups","dhl"]
    return not any(b in (name or "").lower() for b in banned)


class FlightAgent:
    def __init__(self, name="FlightAgent", mode="Online", provider="gemini"):
        self.name = name
        self.mode = mode
        self.provider = provider
        self.prompt = FLIGHT_PROMPT

    def _call_gemini(self, prompt, origin, destination, constraint=None):
        def _fetch():
            api_key = os.getenv("GOOGLE_API_KEY")
            text = f"Origin: {origin}\nDestination: {destination}"
            if constraint:
                text += f"\nConstraint: {constraint}"

            # Static prompt is sent via a cached-content handle (if available)
            # instead of being re-transmitted on every call.
            body = build_gemini_request(self.name, prompt, text)
            resp = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent",
                params={"key": api_key},
                json=body,
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

        # Identical origin/destination/constraint → served from cache, no Gemini tokens spent
        params = {"origin": origin, "destination": destination, "constraint": constraint}
        return call_api("gemini:flight", params, fetch_fn=_fetch)

    def run(self, state):
        if not state.get("origin") or not state.get("destination"):
            return {"error": "Origin or destination missing"}

        constraint = state.get("constraint")

        # Demo mode → rich stubbed round-trip flights showcasing the full schema
        if self.mode == "Demo":
            def _leg(airline, route, dep, arr, dur, price, rating, fit):
                return {
                    "airline": airline, "route": route, "departure": dep, "arrival": arr,
                    "duration": dur, "class_options": ["Economy", "Business"],
                    "baggage_allowance": "15kg check-in, 7kg cabin", "price_range": price,
                    "rating": rating, "fit": fit, "constraint_applied": constraint or "none",
                }
            origin, destination = state["origin"], state["destination"]
            state["flights"] = {
                "outbound": [
                    _leg("Demo Airways", f"{origin} -> {destination}", "06:00", "08:30", "2h 30m", "$", 4.2, "Early birds and budget travelers"),
                    _leg("Demo Skyline", f"{origin} -> {destination}", "13:00", "15:45", "2h 45m", "$$", 4.4, "Families wanting daytime travel"),
                    _leg("Demo Comfort Air", f"{origin} -> {destination}", "18:00", "20:30", "2h 30m", "$$$", 4.6, "Comfort-focused travelers"),
                    _leg("Demo Value Jet", f"{origin} -> {destination}", "22:00", "01:00+1", "3h 0m", "$", 4.0, "Solo/budget-conscious travelers"),
                ],
                "return": [
                    _leg("Demo Airways", f"{destination} -> {origin}", "09:00", "11:30", "2h 30m", "$", 4.2, "Early birds and budget travelers"),
                    _leg("Demo Skyline", f"{destination} -> {origin}", "16:00", "18:45", "2h 45m", "$$", 4.4, "Families wanting daytime travel"),
                    _leg("Demo Comfort Air", f"{destination} -> {origin}", "20:00", "22:30", "2h 30m", "$$$", 4.6, "Comfort-focused travelers"),
                    _leg("Demo Value Jet", f"{destination} -> {origin}", "23:30", "02:30+1", "3h 0m", "$", 4.0, "Solo/budget-conscious travelers"),
                ],
            }
            state["vlog_insights"] = ["🎬 Demo vlog: Flight booking experience", "🎬 Demo vlog: Airport transfer tips"]
            return state

        try:
            # Online mode → Gemini call with prompt + constraint
            flights_text = self._call_gemini(
                self.prompt,
                state["origin"],
                state["destination"],
                constraint
            )

            # Parse Gemini output into structured outbound + return flights
            state["flights"] = parse_roundtrip_flights_output(flights_text)

            # Enrich with AviationStack API
            state = self._enrich_with_api(state)
        except Exception as e:
            return {
                "flights": {"outbound": [], "return": []},
                "vlog_insights": [],
                "error": f"Unable to fetch flight data: {e}"
            }

        # Append vlog insights via RAG (never let a RAG failure wipe the flight results)
        try:
            rag_results = query_videos(state["destination"], ["flights"], mode=self.mode)
            state["vlog_insights"] = summarize_results(rag_results, mode=self.mode)
        except Exception as e:
            print(f"⚠️ RAG error: {e!r}")
            state["vlog_insights"] = []

        return state

    def _enrich_with_api(self, state):
        api_key = os.getenv("AVIATIONSTACK_API_KEY")
        if not api_key:
            return state

        origin_iata = (state["origin"] or "").upper()
        dest_iata = _city_to_iata(state["destination"])

        state["flights"]["outbound"] = self._enrich_leg(state["flights"].get("outbound", []), api_key, origin_iata, dest_iata, state)
        state["flights"]["return"] = self._enrich_leg(state["flights"].get("return", []), api_key, dest_iata, origin_iata, state)
        return state

    def _enrich_leg(self, flights, api_key, dep_iata, arr_iata, state):
        if not flights:
            return flights

        params = {"access_key": api_key, "dep_iata": dep_iata, "arr_iata": arr_iata, "limit": 20}
        try:
            resp = requests.get("http://api.aviationstack.com/v1/flights", params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json().get("data", []) or []

            api_url_map = {}
            for f in data:
                airline_name = (f.get("airline") or {}).get("name") or ""
                if not _is_passenger_airline(airline_name):
                    continue
                url = _google_flights_url(dep_iata, arr_iata, state.get("start_date"), state.get("end_date"))
                api_url_map[airline_name.lower()] = url

            for f in flights:
                airline = (f.get("airline") or "").strip().lower()
                if airline in api_url_map:
                    f["url"] = api_url_map[airline]
            return flights

        except Exception as e:
            print(f"⚠️ Error calling AviationStack: {e!r}")
            return flights
