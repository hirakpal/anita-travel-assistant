class ImpactAssessmentAgent:
    def __init__(self, name="ImpactAssessmentAgent", mode="Online"):
        self.name = name
        self.mode = mode
        self.prompt = """
        You are the Impact Assessment Agent.
        Task: Evaluate disruptions and changes in itinerary.
        Include:
        - Risk factors (flights, hotels, activities, transport, weather, visa, currency, health)
        - Severity (Low, Medium, High)
        - Suggested mitigations
        """

    def run(self, state):
        disruptions = state.get("disruptions", [])
        assessments = []

        # Demo mode → stubbed disruptions
        if self.mode == "Demo":
            state["impact_assessment"] = [
                {"risk": "Demo disruption: flight delay risk", "severity": "Medium", "mitigation": "Rebook flight"}
            ]
            return state

        # Flight disruptions
        if "flights" in state and disruptions:
            assessments.append({
                "risk": "Flight delay or cancellation",
                "severity": "High",
                "mitigation": "Rebook flight, notify hotel, adjust itinerary"
            })

        # Hotel disruptions
        if "hotels" in state and disruptions:
            assessments.append({
                "risk": "Late hotel check-in or overbooking",
                "severity": "Medium",
                "mitigation": "Notify hotel, arrange alternative accommodation"
            })

        # Activity disruptions
        if "activities" in state and disruptions:
            assessments.append({
                "risk": "Activity cancellation due to weather or overbooking",
                "severity": "Medium",
                "mitigation": "Reschedule or choose indoor alternatives"
            })

        # Transport disruptions
        if "transport" in state and disruptions:
            assessments.append({
                "risk": "Traffic delays or metro closures",
                "severity": "Medium",
                "mitigation": "Use alternate routes, buffer travel time"
            })

        # Weather advisories
        if "weather" in state and "advisories" in state["weather"]:
            advisories = state["weather"]["advisories"]
            if advisories and advisories != "No major advisories":
                assessments.append({
                    "risk": f"Weather advisory: {advisories}",
                    "severity": "High",
                    "mitigation": "Reschedule outdoor activities, monitor alerts"
                })

        # Visa issues
        if "visa" in state:
            assessments.append({
                "risk": "Visa processing delays or entry restrictions",
                "severity": "High",
                "mitigation": "Apply early, keep embassy contact handy"
            })

        # Currency/utility issues
        if "utility_insights" in state:
            assessments.append({
                "risk": "Currency exchange fee spikes or SIM unavailability",
                "severity": "Low",
                "mitigation": "Use cards/digital wallets, buy SIM at airport"
            })

        # Health advisories
        if "health" in state:
            assessments.append({
                "risk": "Local health advisory or epidemic",
                "severity": "High",
                "mitigation": "Carry vaccines, insurance, avoid hotspots"
            })

        state["impact_assessment"] = assessments
        return state
