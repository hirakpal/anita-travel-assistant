class EventSubAgent:
    def __init__(self, name="EventSubAgent", mode="Online"):
        self.name = name
        self.mode = mode
        self.prompt = """
        You are the Event Sub-Agent.
        Task: Suggest local events during the tour.
        Include:
        - Event name
        - Date/time
        - Location
        - Highlights
        """

    def run(self, state):
        if not state.get("destination"):
            return {"error": "Destination missing"}

        if self.mode == "Demo":
            state["events"] = [{"name": "Demo Festival", "date": "20 July", "location": "City Square"}]
            return state

        # Stubbed example
        state["events"] = [
            {"name": "Jaipur Literature Festival", "date": "22–26 July", "location": "Diggi Palace", "highlights": "Authors, workshops, cultural shows"},
            {"name": "Local Food Fair", "date": "23 July", "location": "Central Park", "highlights": "Street food, live music"}
        ]
        return state

