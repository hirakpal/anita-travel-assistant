#agents/hotel_agent.py
import os
import requests
import youtube_rag
from prompts.flight_prompt import HOTEL_PROMPT
class HotelAgent:
    def __init__(self, name="HotelAgent", mode="Online", provider="gemini"):
        self.name = name
        self.mode = mode
        self.provider = provider
        self.prompt = HOTEL_PROMPT

    def run(self, state):
        if not state.get("destination"):
            return {"error": "Destination missing"}

        # DEMO MODE → stubbed hotels only
        if self.mode == "Demo":
            state["hotels"] = [
                {"name": "Demo Hotel", "location": "City Center", "price_range": "$100"}
            ]
            state["vlog_insights"] = ["🎬 Demo vlog: Hotel booking highlights"]
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
                                "text": f"{self.prompt}\nDestination: {state['destination']}\nTraveler profile: {state.get('profile','General')}"
                            }]
                        }]
                    },
                    timeout=15
                )
                resp.raise_for_status()
                data = resp.json()
                output_text = data["candidates"][0]["content"]["parts"][0]["text"]

                # For now, store raw Gemini output. Later, parse into structured JSON.
                state["hotels"] = [{"raw_output": output_text}]
            except Exception as e:
                print(f"⚠️ Gemini API error: {e!r}")
                state["hotels"] = [{"error": "Unable to fetch hotels from Gemini"}]

        # Append YouTube RAG insights
        rag_results = youtube_rag.query_videos(state["destination"], ["hotels"], mode=self.mode)
        state["vlog_insights"] = youtube_rag.summarize_results(rag_results, mode=self.mode)

        return state
