import os
import requests
from .alert_sub_agent import AlertSubAgent
from .event_sub_agent import EventSubAgent
from .location_sub_agent import LocationSubAgent
from .news_agent import NewsAgent

class TourAgent:
    def __init__(self, name="TourAgent", mode="Online", provider="gemini"):
        self.name = name
        self.mode = mode
        self.provider = provider
        self.prompt = """
        You are the Tour Organizer Agent.
        Task: Suggest 2–3 tours or attractions based on destination.
        Include:
        - Activity name
        - Type of activity (historical, cultural, adventure, family-friendly)
        - Duration
        - Accessibility (wheelchair access, family suitability, etc.)
        - Price range
        - Guest reviews (rating + highlights)
        - Why it’s popular or relevant.
        If weather alerts or closures are flagged, reroute to alternatives.
        If no destination is provided, return an error message.
        """
        self.alert_agent = AlertSubAgent(mode=mode)
        self.event_agent = EventSubAgent(mode=mode)
        self.location_agent = LocationSubAgent(mode=mode)
        self.news_agent = NewsAgent(mode=mode)

    def run(self, state):
        if "destination" not in state:
            return {"error": "Destination missing"}

        # DEMO MODE
        if self.mode == "Demo":
            state["tours"] = [
                {
                    "name": f"{state['destination']} Demo Heritage Walk",
                    "type": "Historical, cultural",
                    "duration": "2 hours",
                    "accessibility": "Family-friendly",
                    "price_range": "$20–$30 per person",
                    "reviews": {"rating": 4.5, "highlights": ["Great demo guides", "Easy pace"]},
                    "fit": "Perfect for demo travelers"
                }
            ]
            state["tour_summary"] = {"tours": state["tours"]}
            return state

        # ONLINE MODE
        if self.provider == "gemini":
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                state["tours"] = [{"error": "GOOGLE_API_KEY not configured"}]
            else:
                try:
                    resp = requests.post(
                        "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
                        headers={"Authorization": f"Bearer {api_key}"},
                        json={
                            "contents": [{"parts": [{"text": f"{self.prompt}\nDestination: {state['destination']}"}]}]
                        },
                        timeout=15
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    
                    # Safer Parsing
                    if "candidates" in data and len(data["candidates"]) > 0:
                        tours_text = data["candidates"][0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        state["tours"] = [{"raw_output": tours_text}]
                    else:
                        state["tours"] = [{"error": "Empty response from Gemini"}]
                        
                except Exception as e:
                    print(f"⚠️ Gemini API error: {e!r}")
                    state["tours"] = [{"error": "Unable to fetch tours from Gemini"}]

        # Run sub-agents
        state = self.alert_agent.run(state)
        state = self.event_agent.run(state)
        state = self.location_agent.run(state)
        state = self.news_agent.run(state)

        # Consolidated summary
        state["tour_summary"] = {
            "tours": state.get("tours", []),
            "alerts": state.get("alerts", []),
            "events": state.get("events", []),
            "locations": state.get("locations", []),
            "news": state.get("news", [])
        }
        return state
