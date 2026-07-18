class FlightAgent:
    def __init__(self, name):
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
        if "origin" not in state or "destination" not in state:
            return {"error": "Origin or destination missing"}
        
        # Stubbed example output — later you’ll replace with API calls
        return {
            "flights": [
                {
                    "airline": "Air India",
                    "route": f"{state['origin']} → {state['destination']}",
                    "duration": "9h 30m",
                    "class_options": ["Economy", "Business"],
                    "baggage_allowance": "25kg check-in + 7kg cabin",
                    "price_range": "$450–$600",
                    "reviews": {
                        "rating": 4.2,
                        "highlights": [
                            "On-time performance is reliable",
                            "Seats comfortable in Business class",
                            "Food quality praised on long-haul routes"
                        ]
                    },
                    "fit": "Good for mid-range travelers"
                },
                {
                    "airline": "Lufthansa",
                    "route": f"{state['origin']} → {state['destination']}",
                    "duration": "10h 15m",
                    "class_options": ["Economy", "Premium Economy", "Business"],
                    "baggage_allowance": "23kg check-in + 8kg cabin",
                    "price_range": "$550–$750",
                    "reviews": {
                        "rating": 4.5,
                        "highlights": [
                            "Excellent service and staff",
                            "Premium Economy seats highly rated",
                            "Smooth connections at Frankfurt hub"
                        ]
                    },
                    "fit": "Best for comfort-focused travelers"
                }
            ]
        }

