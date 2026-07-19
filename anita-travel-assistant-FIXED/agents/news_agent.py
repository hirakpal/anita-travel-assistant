#agents/news_agent.py
import os
import requests
from prompts.news_prompt import NEWS_PROMPT
from utils.parsers import parse_news_output


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
        api_key = os.getenv("GOOGLE_API_KEY")
        try:
            resp = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "contents": [{
                        "parts": [{
                            "text": f"{self.prompt}\nDestination: {state['destination']}"
                        }]
                    }]
                },
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
            output_text = data["candidates"][0]["content"]["parts"][0]["text"]
            state["news"] = parse_news_output(output_text)
        except Exception as e:
            print(f"⚠️ Gemini API error: {e!r}")
            state["news"] = [{"error": "Unable to fetch news"}]

        return state
