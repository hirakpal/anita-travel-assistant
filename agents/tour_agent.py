class TourAgent:
    def __init__(self, name):
        self.name = name

    def run(self, state):
        if "destination" not in state:
            return {"error": "Destination missing"}
        return {"tours": [f"{state['destination']} Tour 1", f"{state['destination']} Tour 2"]}
