class TransportAgent:
    def __init__(self, name="TransportAgent"):
        self.name = name
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
        return state
