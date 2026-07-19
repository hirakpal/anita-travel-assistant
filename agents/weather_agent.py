#agents/weather_agent.py
import requests
import os
from rag import youtube_rag

class WeatherAgent:
    def __init__(self, name="WeatherAgent", mode="Online", provider="google"):
        """
        mode: "Online" or "Demo"
        provider: "google" or "open-meteo"
        """
        self.name = name
        self.mode = mode
        self.provider = provider

    def run(self, state):
        if "destination" not in state:
            return {"error": "Destination missing"}

        # Demo mode → stubbed forecast only
        if self.mode == "Demo":
            state["weather"] = {
                "forecast": {"temperature": "28°C daytime, 20°C nighttime"},
                "seasonal_notes": "Summer season, warm but pleasant evenings",
                "advisories": "No major travel advisories",
                "reviews": {"rating": 4.3, "highlights": ["July is warm but manageable"]},
                "recommendation": "Carry light clothing and sunscreen."
            }
            state["vlog_insights"] = ["🎬 Demo vlog: Weather tips for summer travel"]
            return state

        # Online mode → choose provider
        if self.provider == "google":
            state = self._fetch_google_weather(state)
        else:
            state = self._fetch_open_meteo(state)

        # Append YouTube RAG insights (never let a RAG failure crash the agent)
        try:
            rag_results = youtube_rag.query_videos(state["destination"], ["weather"], mode=self.mode)
            state["vlog_insights"] = youtube_rag.summarize_results(rag_results, mode=self.mode)
        except Exception as e:
            print(f"⚠️ RAG error: {e!r}")
            state["vlog_insights"] = []

        return state

    def _fetch_google_weather(self, state):
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        try:
            resp = requests.get(
                "https://weather.googleapis.com/v1/weather",
                params={
                    "location": state["destination"],
                    "languageCode": "en",
                    "units": "metric",
                    "key": api_key
                },
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            forecast = data.get("currentConditions", {})
            state["weather"] = {
                "forecast": {
                    "temperature": f"{forecast.get('temperature', 'N/A')}°C",
                    "precipitation": forecast.get("precipitation", "N/A"),
                    "wind": f"{forecast.get('windSpeed', 'N/A')} km/h"
                },
                "seasonal_notes": "Live data from Google Weather API",
                "advisories": data.get("alerts", "No major advisories"),
                "reviews": {"rating": 4.6, "highlights": ["Accurate hyperlocal forecasts"]},
                "recommendation": "Plan activities based on live forecast."
            }
        except Exception as e:
            print(f"⚠️ Google Weather API error: {e!r}")
            state["weather"] = {"error": "Unable to fetch live weather data"}
        return state

    def _fetch_open_meteo(self, state):
        try:
            geo = requests.get(
                f"https://geocoding-api.open-meteo.com/v1/search?name={state['destination']}"
            ).json()
            lat = geo["results"][0]["latitude"]
            lon = geo["results"][0]["longitude"]
        except:
            lat, lon = 19.0760, 72.8777  # fallback: Mumbai

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min"
            f"&timezone=auto"
        )

        try:
            data = requests.get(weather_url).json()
            max_t = max(data["daily"]["temperature_2m_max"])
            min_t = min(data["daily"]["temperature_2m_min"])
            summary = f"Temperature ranges between {min_t:.1f}°C and {max_t:.1f}°C."
        except:
            summary = "Weather unavailable."

        state["weather"] = {
            "forecast": {"temperature": summary},
            "seasonal_notes": "Live data from Open-Meteo",
            "advisories": "Check local advisories for updates",
            "reviews": {"rating": 4.5, "highlights": ["Weather API data accurate"]},
            "recommendation": "Pack accordingly based on forecast."
        }
        return state
