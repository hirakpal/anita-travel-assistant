#agents/news_agent.py
import os
import requests
from prompts.news_prompt import NEWS_PROMPT
from utils.parsers import parse_news_output
from utils.cache import call_api
from utils.prompt_cache import build_gemini_request


class NewsAgent:
    def __init__(self, name="NewsAgent", mode="Online", provider="gemini"):
        self.name = name
        self.mode = mode
        self.provider = provider
        self.prompt = NEWS_PROMPT

    def run(self, state):
        if not state.get("destination"):
            return {"error": "Destination missing"}

        # DEMO MODE → stubbed news only
        if self.mode == "Demo":
            state["news"] = [
                {"headline": "Demo News: Local festival this week", "source": "Demo Source", "date": None, "summary": "Demo summary"}
            ]
            return state

        # ONLINE MODE → Gemini API
        def _fetch():
            api_key = os.getenv("GOOGLE_API_KEY")
            body = build_gemini_request(self.name, self.prompt, f"Destination: {state['destination']}")
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
            # Identical destination → served from cache, no Gemini tokens spent
            output_text = call_api("gemini:news", {"destination": state["destination"]}, fetch_fn=_fetch)
            state["news"] = parse_news_output(output_text)
        except Exception as e:
            print(f"⚠️ Gemini API error: {e!r}")
            state["news"] = [{"error": "Unable to fetch news"}]

        return state
