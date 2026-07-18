class TourAgent:
    def __init__(self, name):
        self.name = name
        self.prompt = """
        You are the Tour Organizer Agent.
        Task: Suggest 2–3 tours or attractions based on destination.
        Include:
        - Activity name
        - Duration
        - Why it’s popular or relevant.
        If weather alerts or closures are flagged, reroute to alternatives.
        If no destination is provided, return an error message.
        """

    def run(self, state):
        if "destination" not in state:
            return {"error": "Destination missing"}
        return {"tours": [f"{state['destination']} Tour 1", f"{state['destination']} Tour 2"]}

