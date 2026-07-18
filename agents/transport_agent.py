class TransportAgent:
    def __init__(self, name):
        self.name = name
        self.prompt = """
        You are the Transport Agent.
        Task: Suggest trains, buses, or local transfers based on destination, arrival, and departure times.
        Include:
        - Mode of transport (train, bus, shuttle, taxi)
        - Departure & arrival times
        - Duration
        - Price range
        - Accessibility (family-friendly, wheelchair access, etc.)
        - Reviews (rating + highlights)
        - Fit with user’s arrival/departure window
        """

    def run(self, state):
        if not all(k in state for k in ["destination", "arrival_time", "departure_time"]):
            return {"error": "Destination, arrival, or departure time missing"}
        
        return {
            "transport": [
                {
                    "mode": "Airport Shuttle Bus",
                    "route": f"Airport → {state['destination']} City Center",
                    "departure": state["arrival_time"],
                    "duration": "45 min",
                    "price_range": "$10–$15",
                    "accessibility": "Family-friendly, luggage space",
                    "reviews": {
                        "rating": 4.4,
                        "highlights": [
                            "Reliable service",
                            "Affordable compared to taxis",
                            "Runs every 30 minutes"
                        ]
                    },
                    "fit": "Matches arrival window"
                },
                {
                    "mode": "Train",
                    "route": f"{state['destination']} City Center → Airport",
                    "departure": state["departure_time"],
                    "duration": "40 min",
                    "price_range": "$12–$18",
                    "accessibility": "Wheelchair accessible",
                    "reviews": {
                        "rating": 4.6,
                        "highlights": [
                            "Fast and punctual",
                            "Comfortable seating",
                            "Good for families"
                        ]
                    },
                    "fit": "Matches departure window"
                }
            ]
        }
