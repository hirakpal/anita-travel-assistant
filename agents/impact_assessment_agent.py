import os
import requests

class ImpactAssessmentAgent:
    def __init__(self, name="ImpactAssessmentAgent", mode="Online", provider="gemini"):
        self.name = name
        self.mode = mode
        self.provider = provider
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

        # DEMO MODE → stubbed disruptions
        if self.mode == "Demo":
            state["impact_assessment"] = [
                {"risk": "Demo disruption: flight delay risk", "severity": "Medium", "mitigation": "Rebook flight"}
            ]
            return state

        # ONLINE MODE → Gemini API
        if self.provider == "gemini":
            api_key = os.getenv("GOOGLE_API_KEY")
            try:
                resp = requests.post(
                    "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "contents": [{
                            "parts": [{
                                "text": f"{self.prompt}\nDisruptions: {disruptions}\nState: {state}"
                            }]
                        }]
                    },
                    timeout=15
                )
                resp.raise_for_status()
                data = resp.json()
                output_text = data["candidates"][0]["content"]["parts"][0]["text"]

                # For now, store raw Gemini output. Later, parse into structured JSON.
                state["impact_assessment"] = [{"raw_output": output_text}]
            except Exception as e:
                print(f"⚠️ Gemini API error: {e!r}")
                state["impact_assessment"] = [{"error": "Unable to fetch impact assessment from Gemini"}]

        return state
