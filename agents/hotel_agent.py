class HotelAgent:
    def __init__(self, name="HotelAgent"):
        self.name = name
        self.prompt = """
        You are the Hotel Agent.
        Task: Suggest 1–2 hotel options based on destination, budget tier, and traveler profile.
        Include:
        - Hotel name
        - Location (distance from airport/center)
        - Room types (Standard, Deluxe, Suite)
        - Amenities (WiFi, Pool, Breakfast)
        - Price range
        - Guest reviews (rating + highlights)
        - Why it fits the user’s profile (budget, family, luxury).
        """

    def run(self, state):
        if not state.get("destination"):
            return {"error": "Destination missing"}

        # Stubbed LLM suggestions
        hotels = [
            {
                "name": "ITC Rajputana Jaipur",
                "location": "2 km from Jaipur Railway Station",
                "room_types": ["Deluxe", "Suite"],
                "amenities": ["WiFi", "Pool", "Breakfast"],
                "price_range": "$120–$180 per night",
                "reviews": {"rating": 4.5, "highlights": ["Excellent service", "Great food", "Central location"]},
                "fit": "Luxury traveler, close to city center"
            },
            {
                "name": "Holiday Inn Jaipur",
                "location": "Near Amer Fort",
                "room_types": ["Standard", "Deluxe"],
                "amenities": ["WiFi", "Gym", "Breakfast"],
                "price_range": "$80–$120 per night",
                "reviews": {"rating": 4.2, "highlights": ["Comfortable rooms", "Good breakfast", "Value for money"]},
                "fit": "Budget‑friendly family option"
            }
        ]
        state["hotels"] = hotels
        return state
