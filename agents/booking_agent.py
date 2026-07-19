#agents/booking_agent.py
import os
import requests
from utils.parsers import parse_booking_output
from prompts.booking_prompt import BOOKING_PROMPT
from utils.cache import call_api
from utils.prompt_cache import build_gemini_request

class BookingAgent:
    def __init__(self, name="BookingAgent", mode="Online", provider="gemini"):
        self.name = name
        self.mode = mode
        self.provider = provider
        self.prompt = BOOKING_PROMPT

    def run(self, state):
        # DEMO MODE → stubbed booking only
        if self.mode == "Demo":
            return {
                "booking": [
                    {
                        "confirmation": "DEMO123",
                        "cancellation_policy": "Demo: Free cancellation until 72 hours",
                        "payment_options": ["Credit Card", "PayPal"],
                        "reviews": {
                            "rating": 4.5,
                            "highlights": ["Demo booking process smooth", "Refunds handled"]
                        },
                        "status": "Demo reservations confirmed for hotel, tours, flights."
                    }
                ]
            }

        # ONLINE MODE → Gemini API
        if self.provider == "gemini":
            def _fetch():
                api_key = os.getenv("GOOGLE_API_KEY")
                body = build_gemini_request(self.name, self.prompt, f"State: {state}")
                resp = requests.post(
                    "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json=body,
                    timeout=15
                )
                resp.raise_for_status()
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]

            try:
                # Identical state → served from cache, no Gemini tokens spent
                output_text = call_api("gemini:booking", {"state": state}, fetch_fn=_fetch)

                # Parse Gemini output into structured list of bookings
                parsed_bookings = parse_booking_output(output_text)
                return {"booking": parsed_bookings}

            except Exception as e:
                print(f"⚠️ Gemini API error: {e!r}")
                return {"booking": [{"error": "Unable to fetch booking confirmation from Gemini"}]}
