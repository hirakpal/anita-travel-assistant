class FoodAgent:
    def __init__(self, name):
        self.name = name
        self.prompt = """
        You are the Food Expert Agent.
        Task: Recommend 2–3 restaurants or food experiences based on destination and food preferences.
        Include:
        - Restaurant name
        - Cuisine type
        - Why it matches the user’s preferences.
        If no destination is provided, return an error message.
        """

    def run(self, state):
        if "destination" not in state:
            return {"error": "Destination missing"}
        return {"food": [f"{state['destination']} Restaurant X", f"{state['destination']} Restaurant Y"]}

