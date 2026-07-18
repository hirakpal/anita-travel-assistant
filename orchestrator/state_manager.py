class StateManager:
    def __init__(self, initial_state=None):
        # Initialize with user inputs
        self.state = initial_state if initial_state else {}

    def update(self, key, value):
        """Update state with agent output"""
        self.state[key] = value

    def get(self, key, default=None):
        """Retrieve value from state"""
        return self.state.get(key, default)

    def has_keys(self, *keys):
        """Check if required keys exist"""
        return all(k in self.state and self.state[k] for k in keys)

    def route(self, agent_name):
        """Decide if agent can run based on state"""
        if agent_name == "hotel":
            return self.has_keys("destination", "budget")
        elif agent_name == "food":
            return self.has_keys("destination", "food_pref")
        elif agent_name == "tour":
            return self.has_keys("destination")
        elif agent_name == "flight":
            return self.has_keys("origin", "destination")
        elif agent_name == "weather":
            return self.has_keys("destination", "dates")
        elif agent_name == "booking":
            return self.has_keys("hotel", "food", "tour", "flight")
        return False
