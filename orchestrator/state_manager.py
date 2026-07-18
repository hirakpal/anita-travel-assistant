import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

class StateManager:
    def __init__(self, initial_state=None):
        self.state = initial_state if initial_state else {}

    def update(self, key, value):
        """Update state with agent output and log it"""
        self.state[key] = value
        logging.info(f"State updated: {key} → {value}")

    def get(self, key, default=None):
        return self.state.get(key, default)

    def has_keys(self, *keys):
        return all(k in self.state and self.state[k] for k in keys)

    def route(self, agent_name):
        """Decide if agent can run based on state"""
        rules = {
            "hotel": ["destination", "budget"],
            "food": ["destination", "food_pref"],
            "tour": ["destination"],
            "flight": ["origin", "destination"],
            "weather": ["destination", "dates"],
            "booking": ["hotel", "food", "tour", "flight"]
        }
        required = rules.get(agent_name, [])
        can_run = self.has_keys(*required)
        logging.info(f"Routing check: {agent_name} → {'RUN' if can_run else 'SKIP'}")
        return can_run
