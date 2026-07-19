#agents/booking_agent.py
import os
import requests
from utils.parsers import parse_booking_output
from prompts.booking_prompt import BOOKING_PROMPT

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
            api_key = os.getenv("GOOGLE_API_KEY")
            try:
                resp = requests.post(
                    "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "contents": [{
                            "parts": [{
                                "text": f"{self.prompt}\nState: {state}"
                            }]
                        }]
                    },
                    timeout=15
                )
                resp.raise_for_status()
                data = resp.json()
                output_text = data["candidates"][0]["content"]["parts"][0]["text"]

                # Parse Gemini output into structured list of bookings
                parsed_bookings = parse_booking_output(output_text)
                return {"booking": parsed_bookings}

            except Exception as e:
                print(f"⚠️ Gemini API error: {e!r}")
                return {"booking": [{"error": "Unable to fetch booking confirmation from Gemini"}]}
