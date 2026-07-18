import youtube_rag

class FoodAgent:
    def __init__(self, name="FoodAgent", mode="Online"):
        self.name = name
        self.mode = mode
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

        # Demo mode → stubbed restaurants only
        if self.mode == "Demo":
            state["restaurants"] = [
                {"name": "Demo Eatery", "cuisine": "Street Food", "price_range": "$10–$20"}
            ]
            state["vlog_insights"] = ["🎬 Demo vlog: Street food highlights"]
            return state

        # Online mode → structured suggestions
        restaurants = [
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
        state["restaurants"] = restaurants

        # Append YouTube RAG insights
        rag_results = youtube_rag.query_videos(state["destination"], ["food"], mode=self.mode)
        state["vlog_insights"] = youtube_rag.summarize_results(rag_results, mode=self.mode)

        return state
