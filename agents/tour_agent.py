class TourAgent:
    def __init__(self, name):
        self.name = name
        self.prompt = """
        You are the Tour Organizer Agent.
        Task: Suggest 2–3 tours or attractions based on destination.
        Include:
        - Activity name
        - Type of activity (historical, cultural, adventure, family-friendly)
        - Duration
        - Accessibility (wheelchair access, family suitability, etc.)
        - Price range
        - Guest reviews (rating + highlights)
        - Why it’s popular or relevant.
        If weather alerts or closures are flagged, reroute to alternatives.
        If no destination is provided, return an error message.
        """

    def run(self, state):
        if "destination" not in state:
            return {"error": "Destination missing"}
        
        # Stubbed example output — later you’ll replace with API calls
        return {
            "tours": [
                {
                    "name": f"{state['destination']} Colosseum Guided Tour",
                    "type": "Historical, cultural",
                    "duration": "2 hours",
                    "accessibility": "Wheelchair accessible, family-friendly",
                    "price_range": "$30–$50 per person",
                    "reviews": {
                        "rating": 4.7,
                        "highlights": [
                            "Skip-the-line access saves time",
                            "Guides are knowledgeable and engaging",
                            "Great for families and history lovers"
                        ]
                    },
                    "fit": "Perfect for cultural travelers"
                },
                {
                    "name": f"{state['destination']} Vatican Museums & Sistine Chapel",
                    "type": "Art, cultural",
                    "duration": "3 hours",
                    "accessibility": "Wheelchair accessible, guided tours available",
                    "price_range": "$40–$60 per person",
                    "reviews": {
                        "rating": 4.8,
                        "highlights": [
                            "Art collection is breathtaking",
                            "Sistine Chapel is a must-see",
                            "Crowded but worth the experience"
                        ]
                    },
                    "fit": "Best for art enthusiasts and first-time visitors"
                }
            ]
        }


