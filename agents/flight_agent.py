#agents/flight_agent.py
import os
import requests
from rag.youtube_rag import query_videos, summarize_results
from prompts.flight_prompt import FLIGHT_PROMPT
from utils.parsers import parse_flights_output
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
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
                headers={"Authorization": f"Bearer {api_key}"},
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
        if not all(k in state for k in ["origin", "destination", "arrival_time", "departure_time"]):
            return {"error": "Origin, destination, arrival, or departure time missing"}
        
        constraint = state.get("constraint")

        # Demo mode → stubbed flights only
        if self.mode == "Demo":
            state["flights"] = [
                {
                    "airline": "Demo Airlines",
                    "route": f"{state['origin']} → {state['destination']}",
                    "price_range": "$500",
                    "constraint_applied": constraint or "none"
                }
            ]
            state["vlog_insights"] = ["🎬 Demo vlog: Flight booking experience"]
            return state

        try:
            # Online mode → Gemini call with prompt + constraint
            flights_text = self._call_gemini(
                self.prompt,
                state["origin"],
                state["destination"],
                constraint
            )

            # Parse Gemini output into structured flights
            flights = parse_flights_output(flights_text)
            state["flights"] = flights

            # Enrich with AviationStack API
            state = self._enrich_with_api(state)

            # Append vlog insights via RAG
            rag_results = query_videos(state["destination"], ["flights"], mode=self.mode)
            state["vlog_insights"] = summarize_results(rag_results, mode=self.mode)

            return state

        except Exception as e:
            return {
                "flights": [],
                "vlog_insights": [],
                "error": f"Unable to fetch flight data: {e}"
            }

    def _enrich_with_api(self, state):
        api_key = os.getenv("AVIATIONSTACK_API_KEY")
        if not api_key:
            return state

        origin_iata = (state["origin"] or "").upper()
        dest_iata = _city_to_iata(state["destination"])

        params = {"access_key": api_key, "dep_iata": origin_iata, "arr_iata": dest_iata, "limit": 20}
        try:
            resp = requests.get("http://api.aviationstack.com/v1/flights", params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json().get("data", []) or []

            api_url_map = {}
            for f in data:
                airline_name = (f.get("airline") or {}).get("name") or ""
                if not _is_passenger_airline(airline_name):
                    continue
                url = _google_flights_url(origin_iata, dest_iata, state.get("start_date"), state.get("end_date"))
                api_url_map[(airline_name.lower(), origin_iata, dest_iata)] = url

            enriched = []
            for f in state["flights"]:
                airline = (f.get("airline") or "").strip()
                key = (airline.lower(), origin_iata, dest_iata)
                if key in api_url_map:
                    f["url"] = api_url_map[key]
                enriched.append(f)
            state["flights"] = enriched
            return state

        except Exception as e:
            print(f"⚠️ Error calling AviationStack: {e!r}")
            return state
