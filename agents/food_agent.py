#agents/food_agent.py
import os
import requests
from rag import youtube_rag
from prompts.food_prompt import FOOD_PROMPT
from utils.cache import call_api
from utils.prompt_cache import build_gemini_request
from utils.parsers import parse_food_json_output
class FoodAgent:
    def __init__(self, name="FoodAgent", mode="Online", provider="gemini"):
        self.name = name
        self.mode = mode
        self.provider = provider
        self.prompt = FOOD_PROMPT

    def run(self, state):
        if "destination" not in state:
            return {"error": "Destination missing"}

        # DEMO MODE → stubbed restaurants only
        if self.mode == "Demo":
            state["restaurants"] = [
                {"name": "Demo Eatery", "cuisine": "Street Food", "price_range": "$10–$20"}
            ]
            state["vlog_insights"] = ["🎬 Demo vlog: Street food highlights"]
            return state

        # ONLINE MODE → Gemini API
        if self.provider == "gemini":
            preferences = state.get("food_pref", "General")
            traveler_type = state.get("traveler_type", "General")

            def _fetch():
                api_key = os.getenv("GOOGLE_API_KEY")
                text = f"Destination: {state['destination']}\nFood preferences: {preferences}\nTraveler type: {traveler_type}"
                body = build_gemini_request(self.name, self.prompt, text)
                resp = requests.post(
                    "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent",
                    params={"key": api_key},
                    json=body,
                    timeout=15
                )
                resp.raise_for_status()
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]

            try:
                # Identical destination/preferences/traveler_type → served from cache, no Gemini tokens spent
                params = {"destination": state["destination"], "preferences": preferences, "traveler_type": traveler_type}
                output_text = call_api("gemini:food", params, fetch_fn=_fetch)
                state["restaurants"] = parse_food_json_output(output_text)
            except Exception as e:
                print(f"⚠️ Gemini API error: {e!r}")
                state["restaurants"] = [{"error": "Unable to fetch restaurants from Gemini"}]

        # Append YouTube RAG insights (never let a RAG failure crash the agent)
        try:
            rag_results = youtube_rag.query_videos(state["destination"], ["food"], mode=self.mode)
            state["vlog_insights"] = youtube_rag.summarize_results(rag_results, mode=self.mode)
        except Exception as e:
            print(f"⚠️ RAG error: {e!r}")
            state["vlog_insights"] = []

        return state
