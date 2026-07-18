class FlightAgent:
    def __init__(self, name="FlightAgent"):
        self.name = name
        self.prompt = """
        You are the Flight Agent.
        Task: Suggest 1–2 flight options based on origin, destination, and budget tier.
        Include:
        - Airline name
        - Flight duration
        - Class options (Economy, Premium, Business)
        - Baggage allowance
        - Price range
        - Passenger reviews (rating + highlights)
        - Why it fits the user’s profile (budget, family, luxury).
        If origin or destination is missing, return an error message.
        """

    def run(self, state):
        if not all(k in state for k in ["origin", "destination", "arrival_time", "departure_time"]):
            return {"error": "Origin, destination, arrival, or departure time missing"}

        # Step 1: Generate LLM-style structured flights (prompt-driven)
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

        # Step 2: Enrich with API (AviationStack + Google Flights URLs)
        return self._enrich_with_api(state)

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

            # Enrich LLM flights with real URLs
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
