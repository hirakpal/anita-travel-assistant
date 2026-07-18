import os, requests
from agents.news_agent import NewsAgent
from utils.parsers import (
    parse_tours_output,
    parse_alerts_output,
    parse_events_output,
    parse_locations_output
)

class TourAgent:
    def __init__(self, name="TourAgent", mode="Online", provider="gemini"):
        self.name = name
        self.mode = mode
        self.provider = provider
        # Plug in NewsAgent (demo or online)
        self.news_agent = NewsAgent(mode="online" if mode == "Online" else "demo")

        # Prompts for Gemini
        self.prompt_tours = """
        You are the Tour Agent.
        Task: Suggest 2–3 tours based on destination and traveler profile.
        Include: name, type, duration, price range, reviews, fit.
        Return strictly in JSON format.
        """
        self.prompt_alerts = """
        You are the Alert SubAgent.
        Task: Provide travel advisories (weather, strikes, health alerts).
        Include: type, message, severity.
        Return strictly in JSON format.
        """
        self.prompt_events = """
        You are the Event SubAgent.
        Task: Suggest local events (festivals, concerts, exhibitions).
        Include: name, date, location, description, price range, reviews.
        Return strictly in JSON format.
        """
        self.prompt_locations = """
        You are the Location SubAgent.
        Task: Recommend attractions/landmarks.
        Include: name, type, opening_hours, price_range, reviews.
        Return strictly in JSON format.
        """

    def _call_gemini(self, prompt, destination):
        api_key = os.getenv("GOOGLE_API_KEY")
        resp = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"contents": [{"parts": [{"text": f"{prompt}\nDestination: {destination}"}]}]},
            timeout=15
        )
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    def run(self, state):
        destination = state.get("destination", "travel")

        # DEMO MODE
        if self.mode == "Demo":
            return {
                "tour_summary": {
                    "tours": [{"name": "Demo Tour", "type": "Cultural"}],
                    "alerts": [{"type": "General", "message": "Demo alert"}],
                    "events": [{"name": "Demo Event"}],
                    "locations": [{"name": "Demo Location"}],
                    "news": self.news_agent.get_news(destination)
                }
            }

        # ONLINE MODE
        try:
            # Tours
            tours_text = self._call_gemini(self.prompt_tours, destination)
            tours = parse_tours_output(tours_text)

            # Alerts
            alerts_text = self._call_gemini(self.prompt_alerts, destination)
            alerts = parse_alerts_output(alerts_text)

            # Events
            events_text = self._call_gemini(self.prompt_events, destination)
            events = parse_events_output(events_text)

            # Locations
            locations_text = self._call_gemini(self.prompt_locations, destination)
            locations = parse_locations_output(locations_text)

            # News → via NewsAgent (SearchAPI.io + RSS + fallback)
            news = self.news_agent.get_news(destination)

            return {
                "tour_summary": {
                    "tours": tours,
                    "alerts": alerts,
                    "events": events,
                    "locations": locations,
                    "news": news
                }
            }

        except Exception as e:
            print(f"⚠️ TourAgent error: {e!r}")
            return {"tour_summary": {"error": "Unable to fetch tour data"}}
