class WeatherAgent:
    def __init__(self, name):
        self.name = name
        self.prompt = """
        You are the Weather Agent.
        Task: Given a destination and travel dates, check climate conditions.
        Include:
        - Forecast details (temperature, precipitation, wind)
        - Seasonal notes (e.g., monsoon, peak summer, winter holidays)
        - Travel advisories (storms, closures, health alerts)
        - Traveler reviews (rating + highlights like 'July is hot but great for sightseeing')
        - Recommendation (best activities or precautions based on weather)
        If no destination is provided, return an error message.
        """

    def run(self, state):
        if "destination" not in state:
            return {"error": "Destination missing"}
        
        # Stubbed example output — later you’ll replace with real weather API calls
        return {
            "weather": {
                "forecast": {
                    "temperature": "28°C daytime, 20°C nighttime",
                    "precipitation": "10% chance of rain",
                    "wind": "Light breeze, 8 km/h"
                },
                "seasonal_notes": "Summer season, warm but pleasant evenings",
                "advisories": "No major travel advisories",
                "reviews": {
                    "rating": 4.3,
                    "highlights": [
                        "July is warm but manageable",
                        "Evenings are perfect for outdoor dining",
                        "Occasional showers add freshness"
                    ]
                },
                "recommendation": "Carry light clothing, sunscreen, and a small umbrella."
            }
        }

