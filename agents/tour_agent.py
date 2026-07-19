#agents/tour_agent.py
import os, requests
import concurrent.futures
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

    def _call_gemini(self, prompt, destination, service, traveler_type=None, travel_party=None, constraint=None):
        dynamic_text = f"Destination: {destination}"
        if traveler_type:
            dynamic_text += f"\nTraveler type: {traveler_type}"
        if travel_party:
            dynamic_text += f"\nTravel party: {travel_party}"
        if constraint:
            dynamic_text += f"\nTraveler feedback to incorporate: {constraint}"

        def _fetch():
            api_key = os.getenv("GOOGLE_API_KEY")
            body = build_gemini_request(f"{self.name}:{service}", prompt, dynamic_text)
            resp = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent",
                params={"key": api_key},
                json=body,
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

        # Identical inputs per sub-call → served from cache, no Gemini tokens spent
        params = {"destination": destination, "traveler_type": traveler_type, "travel_party": travel_party, "constraint": constraint}
        return call_api(f"gemini:tour:{service}", params, fetch_fn=_fetch)

    def run(self, state):
        if not state.get("destination"):
            return {"error": "Destination missing"}

        if self.mode == "Demo":
            destination = state["destination"]
            return {
                "tour_summary": {
                    "tours": [
                        {
                            "title": f"{destination} Heritage Walking Tour", "location": f"Old City, {destination}",
                            "price": "$$", "rating": 4.7, "popularity": "Demo: most-booked cultural tour",
                            "duration": "3 hours", "accessibility_notes": "Demo: some uneven cobblestone paths",
                            "fit": "Great for culture lovers and families",
                            "what_to_expect": "Demo: guided walk through historic landmarks and local markets",
                            "best_time": "Early morning", "tips": "Demo: wear comfortable shoes",
                        },
                        {
                            "title": f"{destination} Family Adventure Park", "location": f"Adventure Zone, {destination}",
                            "price": "$$", "rating": 4.5, "popularity": "Demo: top pick for families",
                            "duration": "4 hours", "accessibility_notes": "Demo: stroller-friendly paths available",
                            "fit": "Great for families with young children",
                            "what_to_expect": "Demo: interactive rides and educational exhibits",
                            "best_time": "Weekday mornings", "tips": "Demo: book tickets online for skip-the-line access",
                        },
                        {
                            "title": f"{destination} Sunset Viewpoint Tour", "location": f"Hilltop, {destination}",
                            "price": "$", "rating": 4.6, "popularity": "Demo: highly rated scenic experience",
                            "duration": "2 hours", "accessibility_notes": "Demo: accessible by vehicle, minimal walking",
                            "fit": "Great for seniors and couples",
                            "what_to_expect": "Demo: panoramic sunset views with a local guide",
                            "best_time": "Sunset", "tips": "Demo: bring a light jacket for the evening breeze",
                        },
                        {
                            "title": f"{destination} Solo Explorer Bazaar Tour", "location": f"Market District, {destination}",
                            "price": "$", "rating": 4.4, "popularity": "Demo: popular with solo travelers",
                            "duration": "2.5 hours", "accessibility_notes": "Demo: busy, well-lit pedestrian streets",
                            "fit": "Great for solo travelers, including solo female travelers",
                            "what_to_expect": "Demo: small-group guided shopping and street food sampling in a well-populated area",
                            "best_time": "Daytime", "tips": "Demo: small groups only, book ahead",
                        },
                    ],
                    "alerts": [
                        {"type": "Weather", "message": "Demo: mild weather expected, no major concerns", "severity": "Low"},
                        {"type": "Local Disruption", "message": "Demo: minor road works near downtown", "severity": "Low"},
                    ],
                    "events": [
                        {"name": "Demo: Local Cultural Festival", "date": None, "location": destination, "description": "Demo event"},
                    ],
                    "locations": [
                        {"name": f"Demo: {destination} Landmark", "type": "Landmark", "opening_hours": "9am-6pm", "price_range": "$"},
                    ],
                    "news": [
                        {"headline": f"Demo: {destination} tourism update", "source": "Demo Source", "date": None, "summary": "Demo summary"},
                    ],
                }
            }

        traveler_type = state.get("traveler_type", "General")
        travel_party = state.get("travel_party")
        constraint = state.get("constraint")

        destination = state["destination"]
        # These 5 sub-calls are independent — run them concurrently instead
        # of paying 5x sequential Gemini round-trip latency.
        sub_calls = {
            "tours": (self.prompt_tours, {"traveler_type": traveler_type, "travel_party": travel_party, "constraint": constraint}, parse_tours_output),
            "alerts": (self.prompt_alerts, {}, parse_alerts_output),
            "events": (self.prompt_events, {}, parse_events_output),
            "locations": (self.prompt_locations, {}, parse_locations_output),
            "news": (self.prompt_news, {}, parse_news_output),
        }

        results = {}
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(sub_calls)) as executor:
                futures = {
                    executor.submit(self._call_gemini, prompt, destination, service, **kwargs): (service, parser)
                    for service, (prompt, kwargs, parser) in sub_calls.items()
                }
                for future in concurrent.futures.as_completed(futures):
                    service, parser = futures[future]
                    results[service] = parser(future.result())

            return {
                "tour_summary": {
                    "tours": results["tours"],
                    "alerts": results["alerts"],
                    "events": results["events"],
                    "locations": results["locations"],
                    "news": results["news"],
                }
            }

        except Exception as e:
            print(f"⚠️ Gemini API error: {e!r}")
            return {"tour_summary": {"error": "Unable to fetch tour data"}}
