class WeatherAgent:
    def __init__(self, name):
        self.name = name
        self.prompt = """
        You are the Weather Agent.
        Task: Given a destination and travel dates, check climate conditions.
        - If severe weather or closures are detected, alert ANITA and reroute to Tour Agent.
        - Otherwise, return a simple weather summary.
        """

    def run(self, state):
        if "destination" not in state:
            return {"error": "Destination missing"}
        return {"weather": f"Weather in {state['destination']} is sunny with mild temperatures."}
