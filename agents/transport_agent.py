import sim_currency_rag

class TransportAgent:
    def __init__(self, name="TransportAgent", mode="Online"):
        self.name = name
        self.mode = mode
        self.prompt = """
        You are the Transport Agent.
        Task: Suggest local transport options between hotel, airport, and activities.
        Include:
        - Mode (Cab, Metro, Bus, Rental Car)
        - Duration
        - Price range
        - Availability
        - Reviews (rating + highlights)
        - Why it fits the user’s profile (budget, convenience, family).
        """

    def run(self, state):
        if not state.get("origin") or not state.get("destination"):
            return {"error": "Origin or destination missing"}

        # Demo mode → stubbed transport only
        if self.mode == "Demo":
            state["transport"] = [
                {"mode": "Demo Cab", "duration": "15 min", "price_range": "$10"}
            ]
            state["utility_insights"] = ["🎬 Demo SIM info: Prepaid SIM available at airport"]
            return state

        # Online mode → structured suggestions
        transports = [
            {
                "mode": "Cab",
                "duration": "20 min",
                "price_range": "$10–$15",
                "availability": "24/7",
                "reviews": {"rating": 4.3, "highlights": ["Reliable drivers", "Comfortable rides"]},
                "fit": "Convenient for families"
            },
            {
                "mode": "Metro",
                "duration": "25 min",
                "price_range": "$2–$3",
                "availability": "6 AM – 11 PM",
                "reviews": {"rating": 4.0, "highlights": ["Fast", "Budget‑friendly"]},
                "fit": "Best for solo travelers on budget"
            }
        ]
        state["transport"] = transports

        # Append SIM/Currency RAG insights
        rag_results = sim_currency_rag.query_entries(state["destination"], ["transport"], mode=self.mode)
        state["utility_insights"] = sim_currency_rag.summarize_results(rag_results, mode=self.mode)

        return state
