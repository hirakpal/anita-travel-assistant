# orchestrator/state_manager.py
import logging
import json

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

class StateManager:
    def __init__(self, initial_state=None):
        self.state = initial_state if initial_state else {}

    def update(self, key, value):
        """Update state with agent output and log it"""
        self.state[key] = value
        logging.info(json.dumps({"event": "state_update", "key": key, "value": str(value)}))

    def get(self, key, default=None):
        return self.state.get(key, default)

    def has_keys(self, *keys):
        return all(k in self.state and self.state[k] for k in keys)

    def route(self, agent_name, route_manager=None):
        """
        Decide if agent can run based on state.
        If a RouteManager is provided, delegate routing logic there.
        """
        if route_manager:
            can_run = route_manager.route(agent_name, self.state)
        else:
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

        logging.info(json.dumps({"event": "routing_check", "agent": agent_name, "result": "RUN" if can_run else "SKIP"}))
        return can_run

    def apply_alternates(self, alternates: dict):
        """
        Update state with alternate constraints flagged by ImpactAssessmentAgent.
        """
        for agent, constraint in alternates.items():
            self.state[f"{agent}_constraint"] = constraint
            logging.info(json.dumps({"event": "alternate_applied", "agent": agent, "constraint": constraint}))
