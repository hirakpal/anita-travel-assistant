class FoodAgent:
    def __init__(self, name):
        self.name = name

    def run(self, state):
        if "destination" not in state:
            return {"error": "Destination missing"}
        return {"food": [f"{state['destination']} Restaurant X", f"{state['destination']} Restaurant Y"]}
