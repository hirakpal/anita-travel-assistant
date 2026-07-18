class ImpactAssessmentAgent:
    def __init__(self, name="ImpactAssessmentAgent"):
        self.name = name
        self.prompt = """
        You are the Impact Assessment Agent.
        Task: Evaluate disruptions and changes in itinerary.
        Include:
        - Risk factors (late check-in, missed dinner, traffic delays)
        - Severity (Low, Medium, High)
        - Suggested mitigations
        """

    def run(self, state):
        disruptions = state.get("disruptions", [])
        assessments = []
        for d in disruptions:
            assessments.append({
                "risk": "Late hotel check-in",
                "severity": "Medium",
                "mitigation": "Notify hotel, arrange late check-in"
            })
        state["impact_assessment"] = assessments
        return state
