class FoodAgent:
    def __init__(self, name):
        self.name = name
        self.prompt = """
        You are the Food Expert Agent.
        Task: Recommend 2–3 restaurants or food experiences based on destination and food preferences.
        Include:
        - Restaurant name
        - Cuisine type
        - Dietary options (vegetarian, vegan, gluten-free, etc.)
        - Seating style (casual, fine dining, outdoor, family-friendly)
        - Price range
        - Guest reviews (rating + highlights)
        - Why it matches the user’s preferences.
        If no destination is provided, return an error message.
        """

    def run(self, state):
        if "destination" not in state:
            return {"error": "Destination missing"}
        
        # Stubbed example output — later you’ll replace with API calls
        return {
            "food": [
                {
                    "name": f"{state['destination']} Trattoria Roma",
                    "cuisine": "Italian, local specialties",
                    "dietary_options": ["Vegetarian", "Vegan"],
                    "seating": "Casual indoor & outdoor seating",
                    "price_range": "$20–$40 per person",
                    "reviews": {
                        "rating": 4.6,
                        "highlights": [
                            "Authentic Roman pasta dishes",
                            "Vegetarian options praised",
                            "Outdoor seating with great atmosphere"
                        ]
                    },
                    "fit": "Perfect for couples and food lovers"
                },
                {
                    "name": f"{state['destination']} Green Garden Eatery",
                    "cuisine": "Fusion, healthy dining",
                    "dietary_options": ["Vegan", "Gluten-free"],
                    "seating": "Family-friendly casual dining",
                    "price_range": "$15–$25 per person",
                    "reviews": {
                        "rating": 4.2,
                        "highlights": [
                            "Popular with health-conscious travelers",
                            "Great vegan desserts",
                            "Friendly staff and quick service"
                        ]
                    },
                    "fit": "Best for families and budget-conscious travelers"
                }
            ]
        }

