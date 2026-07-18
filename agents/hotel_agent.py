class HotelAgent:
    def __init__(self, name):
        self.name = name

    def run(self, state):
        if "destination" not in state:
            return {"error": "Destination missing"}
        return {"hotels": [f"{state['destination']} Hotel A", f"{state['destination']} Hotel B"]}
