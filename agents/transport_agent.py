#agents/transport_agent.py
import os
import requests
from rag import sim_currency_rag
from prompts.transport_prompt import TRANSPORT_PROMPT
from utils.cache import call_api
from utils.prompt_cache import build_gemini_request
from utils.parsers import parse_transport_json_output
class TransportAgent:
    def __init__(self, name="TransportAgent", mode="Online", provider="gemini"):
        self.name = name
        self.mode = mode
        self.provider = provider
        self.prompt = TRANSPORT_PROMPT

    def run(self, state):
        if not state.get("origin") or not state.get("destination"):
            return {"error": "Origin or destination missing"}

        # DEMO MODE → rich stubbed transport options showcasing the full schema
        if self.mode == "Demo":
            state["transport"] = [
                {"name": "Demo Metro", "price": "$", "rating": 4.6, "popularity": "Demo: fastest, budget-friendly transit",
                 "distance": "10 km", "duration": "20 min"},
                {"name": "Demo Cab (App-based)", "price": "$$", "rating": 4.4, "popularity": "Demo: convenient door-to-door option",
                 "distance": "12 km", "duration": "25 min"},
                {"name": "Demo Private Car", "price": "$$$", "rating": 4.7, "popularity": "Demo: most comfortable, best for families/seniors",
                 "distance": "12 km", "duration": "22 min"},
                {"name": "Demo Public Bus", "price": "$", "rating": 4.0, "popularity": "Demo: cheapest, scenic route",
                 "distance": "14 km", "duration": "40 min"},
            ]
            state["utility_insights"] = ["🎬 Demo SIM info: Prepaid SIM available at airport", "🎬 Demo currency info: ATMs widely available"]
            return state

        # ONLINE MODE → Gemini API + RAG
        if self.provider == "gemini":
            constraint = state.get("constraint")

            def _fetch():
                api_key = os.getenv("GOOGLE_API_KEY")
                text = f"Origin: {state['origin']}\nDestination: {state['destination']}"
                if constraint:
                    text += f"\nTraveler feedback to incorporate: {constraint}"
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
                # Identical origin/destination/constraint → served from cache, no Gemini tokens spent
                params = {"origin": state["origin"], "destination": state["destination"], "constraint": constraint}
                output_text = call_api("gemini:transport", params, fetch_fn=_fetch)
                state["transport"] = parse_transport_json_output(output_text)
            except Exception as e:
                print(f"⚠️ Gemini API error: {e!r}")
                state["transport"] = [{"error": "Unable to fetch transport options from Gemini"}]

        # Append SIM/Currency RAG insights (never let a RAG failure crash the agent)
        try:
            rag_results = sim_currency_rag.query_entries(state["destination"], ["transport"], mode=self.mode)
            state["utility_insights"] = sim_currency_rag.summarize_results(rag_results, mode=self.mode)
        except Exception as e:
            print(f"⚠️ RAG error: {e!r}")
            state["utility_insights"] = []

        return state
