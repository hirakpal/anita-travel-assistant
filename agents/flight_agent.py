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
        if not all(k in state for k in ["origin", "destination", "arrival_time", "departure_time"]):
            return {"error": "Origin, destination, arrival, or departure time missing"}
        
        # Stubbed example output — later you’ll replace with API calls
        return {
            "flights": [
                {
                    "airline": "Air India",
                    "route": f"{state['origin']} → {state['destination']}",
                    "departure": "12 Aug, 6:00 AM IST",
                    "arrival": state["arrival_time"],
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
                    "reviews": {
                        "rating": 4.5,
                        "highlights": [
                            "Excellent service and staff",
                            "Premium Economy seats highly rated",
                            "Smooth connections at Frankfurt hub"
                        ]
                    },
                    "fit": "Matches requested arrival window"
                }
            ]
        }

