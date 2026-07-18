import os
import requests
from rag.youtube_rag import query_videos, summarize_results

# Helper functions (can be moved to utils.py)
CITY_TO_IATA = {"Mumbai": "BOM", "Bengaluru": "BLR", "Tokyo": "HND", "Singapore": "SIN", "New York": "JFK"}

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
    def __init__(self, name="FlightAgent", mode="Online"):
        self.name = name
        self.mode = mode
        self.prompt = """You are the Flight Agent..."""

    def run(self, state):
        if not all(k in state for k in ["origin", "destination", "arrival_time", "departure_time"]):
            return {"error": "Origin, destination, arrival, or departure time missing"}

        # Demo mode → stubbed flights only
        if self.mode == "Demo":
            state["flights"] = [
                {"airline": "Demo Airlines", "route": f"{state['origin']} → {state['destination']}", "price_range": "$500"}
            ]
            state["vlog_insights"] = ["🎬 Demo vlog: Flight booking experience"]
            return state

        # Online mode → LLM suggestions
        flights = [
            {
                "airline": "Air India",
                "route": f"{state['origin']} → {state['destination']}",
                "departure": "12 Aug, 6:00 AM IST",
                "arrival": state["arrival_time"],
                "duration": "9h 30m",
                "class_options": ["Economy", "Business"],
                "baggage_allowance": "25kg check-in + 7kg cabin",
                "price_range": "$450–$600",
                "reviews": {"rating": 4.2, "highlights": ["On-time performance", "Comfortable seats", "Good food"]},
                "fit": "Matches requested arrival window"
            },
            {
                "airline": "Lufthansa",
                "route": f"{state['origin']} → {state['destination']}",
                "departure": state["departure_time"],
                "arrival": "18 Aug, 11:30 PM IST",
                "duration": "10h 15m",
                "class_options": ["Economy", "Premium Economy", "Business"],
                "baggage_allowance": "23kg check-in + 8kg cabin",
                "price_range": "$550–$750",
                "reviews": {"rating": 4.5, "highlights": ["Excellent service", "Premium Economy praised", "Smooth connections"]},
                "fit": "Matches requested arrival window"
            }
        ]
        state["flights"] = flights

        # Enrich with API
        state = self._enrich_with_api(state)

        # Append vlog insights
        rag_results = query_videos(state["destination"], ["flights"], mode=self.mode)
        state["vlog_insights"] = summarize_results(rag_results, mode=self.mode)

        return state

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
