class AlertSubAgent:
    def __init__(self, name="AlertSubAgent", mode="Online"):
        self.name = name
        self.mode = mode
        self.prompt = """
        You are the Alert Sub-Agent.
        Task: Monitor and surface alerts relevant to the tour.
        Include:
        - Weather warnings
        - Transport strikes
        - Health advisories
        - Safety/security alerts
        """

    def run(self, state):
        if self.mode == "Demo":
            state["alerts"] = ["🎬 Demo alert: Metro strike expected tomorrow"]
            return state

        alerts = []
        if "weather" in state and "advisories" in state["weather"]:
            alerts.append(f"Weather advisory: {state['weather']['advisories']}")
        if "impact_assessment" in state:
            for impact in state["impact_assessment"]:
                if impact["severity"] == "High":
                    alerts.append(f"High severity risk: {impact['risk']}")
        state["alerts"] = alerts
        return state

