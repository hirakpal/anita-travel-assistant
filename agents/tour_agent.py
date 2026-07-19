#agents/tour_agent.py
import os, requests
from utils.parsers import (
    parse_tours_output,
    parse_alerts_output,
    parse_events_output,
    parse_locations_output,
    parse_news_output
)
from prompts.tour_prompt import TOUR_PROMPT
from prompts.alerts_prompt import ALERTS_PROMPT
from prompts.events_prompt import EVENTS_PROMPT
from prompts.locations_prompt import LOCATIONS_PROMPT
from prompts.news_prompt import NEWS_PROMPT
from utils.cache import call_api
from utils.prompt_cache import build_gemini_request

class TourAgent:
    def __init__(self, name="TourAgent", mode="Online", provider="gemini"):
        self.name = name
        self.mode = mode
        self.provider = provider
        self.prompt_tours = TOUR_PROMPT
        self.prompt_alerts = ALERTS_PROMPT
        self.prompt_events = EVENTS_PROMPT
        self.prompt_locations = LOCATIONS_PROMPT
        self.prompt_news = NEWS_PROMPT

    def _call_gemini(self, prompt, destination, service):
        def _fetch():
            api_key = os.getenv("GOOGLE_API_KEY")
            body = build_gemini_request(f"{self.name}:{service}", prompt, f"Destination: {destination}")
            resp = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
                headers={"Authorization": f"Bearer {api_key}"},
                json=body,
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

        # Identical destination per sub-call → served from cache, no Gemini tokens spent
        return call_api(f"gemini:tour:{service}", {"destination": destination}, fetch_fn=_fetch)

    def run(self, state):
        if not state.get("destination"):
            return {"error": "Destination missing"}

        if self.mode == "Demo":
            return {
                "tour_summary": {
                    "tours": [{"name": "Demo Tour", "type": "Cultural"}],
                    "alerts": [{"type": "General", "message": "Demo alert"}],
                    "events": [{"name": "Demo Event"}],
                    "locations": [{"name": "Demo Location"}],
                    "news": [{"headline": "Demo News"}]
                }
            }

        try:
            # Tours
            tours_text = self._call_gemini(self.prompt_tours, state["destination"], "tours")
            tours = parse_tours_output(tours_text)

            # Alerts
            alerts_text = self._call_gemini(self.prompt_alerts, state["destination"], "alerts")
            alerts = parse_alerts_output(alerts_text)

            # Events
            events_text = self._call_gemini(self.prompt_events, state["destination"], "events")
            events = parse_events_output(events_text)

            # Locations
            locations_text = self._call_gemini(self.prompt_locations, state["destination"], "locations")
            locations = parse_locations_output(locations_text)

            # News
            news_text = self._call_gemini(self.prompt_news, state["destination"], "news")
            news = parse_news_output(news_text)

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
            print(f"⚠️ Gemini API error: {e!r}")
            return {"tour_summary": {"error": "Unable to fetch tour data"}}
