class FlightAgent:
    def __init__(self, name):
        self.name = name
        self.prompt = """
        You are the Flight Agent.
        Task: Suggest 1–2 flight options based on origin, destination, and budget tier.
        Include:
        - Airline
        - Duration
        - Approximate cost.
        If origin or destination is missing, return an error message.
        """

    def run(self, state):
        if "origin" not in state or "destination" not in state:
            return {"error": "Origin or destination missing"}
        return {"flights": [f"Flight from {state['origin']} to {state['destination']}"]}

