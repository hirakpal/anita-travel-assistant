class HotelAgent:
    def __init__(self, name):
        self.name = name
        self.prompt = """
        You are the Hotel Expert Agent.
        Task: Suggest 2–3 hotels based on destination, budget tier, and companions.
        Include:
        - Hotel name
        - Location
        - Room details (size, type, bed options)
        - Amenities (WiFi, pool, gym, breakfast, etc.)
        - Parking availability (on-site, valet, free/paid)
        - Approximate price range
        - Why it fits the user’s profile (budget, family, luxury).
        If no destination is provided, return an error message.
        """

    def run(self, state):
        if "destination" not in state:
            return {"error": "Destination missing"}
        
        # Stubbed example output — later you’ll replace with API calls
        return {
            "hotels": [
                {
                    "name": f"{state['destination']} Grand Palace",
                    "location": "City Center",
                    "room_details": "Deluxe Room, King Bed, 35 sqm",
                    "amenities": ["Free WiFi", "Pool", "Gym", "Breakfast included"],
                    "parking": "Free on-site parking",
                    "price_range": "$120–$150 per night",
                    "fit": "Good for mid-range couples"
                },
                {
                    "name": f"{state['destination']} Budget Inn",
                    "location": "Near Airport",
                    "room_details": "Standard Room, Twin Beds, 20 sqm",
                    "amenities": ["WiFi", "Breakfast optional"],
                    "parking": "Paid parking available",
                    "price_range": "$50–$70 per night",
                    "fit": "Best for budget travelers"
                }
            ]
        }


