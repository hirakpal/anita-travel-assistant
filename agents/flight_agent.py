class FlightAgent:
    def __init__(self, name):
        self.name = name

    def run(self, state):
        if "origin" not in state or "destination" not in state:
            return {"error": "Origin or destination missing"}
        return {"flights": [f"Flight from {state['origin']} to {state['destination']}"]}
