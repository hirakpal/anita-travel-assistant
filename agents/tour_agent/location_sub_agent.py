class LocationSubAgent:
    def __init__(self, name="LocationSubAgent", mode="Online"):
        self.name = name
        self.mode = mode
        self.prompt = """
        You are the Location Sub-Agent.
        Task: Recommend must-visit locations.
        Include:
        - Attraction name
        - Distance from hotel/center
        - Opening hours
        - Reviews
        """

    def run(self, state):
        if not state.get("destination"):
            return {"error": "Destination missing"}

        if self.mode == "Demo":
            state["locations"] = [{"name": "Demo Fort", "distance": "5 km", "hours": "9 AM – 5 PM"}]
            return state

        state["locations"] = [
            {"name": "Amber Fort", "distance": "11 km from city center", "hours": "8 AM – 5:30 PM", "reviews": {"rating": 4.7, "highlights": ["Beautiful architecture", "Great views"]}},
            {"name": "Hawa Mahal", "distance": "2 km from hotel", "hours": "9 AM – 4:30 PM", "reviews": {"rating": 4.5, "highlights": ["Iconic landmark", "Photogenic façade"]}}
        ]
        return state

