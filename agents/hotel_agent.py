class HotelAgent:
    def __init__(self, name):
        self.name = name
        self.prompt = """
        You are the Hotel Expert Agent.
        Task: Suggest 2–3 hotels based on destination, budget tier, and companions.
        Include:
        - Hotel name
        - Location
        - Approximate price range
        - Why it fits the user’s profile (budget, family, luxury).
        If no destination is provided, return an error message.
        """

    def run(self, state):
        if "destination" not in state:
            return {"error": "Destination missing"}
        return {"hotels": [f"{state['destination']} Hotel A", f"{state['destination']} Hotel B"]}

