#agents/hotel_agent.py
import os
import requests
from rag import youtube_rag
from prompts.hotel_prompt import HOTEL_PROMPT
from utils.cache import call_api
from utils.prompt_cache import build_gemini_request
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
            profile = state.get("profile", "General")

            def _fetch():
                api_key = os.getenv("GOOGLE_API_KEY")
                text = f"Destination: {state['destination']}\nTraveler profile: {profile}"
                body = build_gemini_request(self.name, self.prompt, text)
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
                # Identical destination/profile → served from cache, no Gemini tokens spent
                params = {"destination": state["destination"], "profile": profile}
                output_text = call_api("gemini:hotel", params, fetch_fn=_fetch)

                # For now, store raw Gemini output. Later, parse into structured JSON.
                state["hotels"] = [{"raw_output": output_text}]
            except Exception as e:
                print(f"⚠️ Gemini API error: {e!r}")
                state["hotels"] = [{"error": "Unable to fetch hotels from Gemini"}]

        # Append YouTube RAG insights (never let a RAG failure crash the agent)
        try:
            rag_results = youtube_rag.query_videos(state["destination"], ["hotels"], mode=self.mode)
            state["vlog_insights"] = youtube_rag.summarize_results(rag_results, mode=self.mode)
        except Exception as e:
            print(f"⚠️ RAG error: {e!r}")
            state["vlog_insights"] = []

        return state
