import os
import requests
import sim_currency_rag

class TransportAgent:
    def __init__(self, name="TransportAgent", mode="Online", provider="gemini"):
        self.name = name
        self.mode = mode
        self.provider = provider
        self.prompt = """
        You are the Transport Agent.
        Task: Suggest local transport options between hotel, airport, and activities.
        Include:
        - Mode (Cab, Metro, Bus, Rental Car)
        - Duration
        - Price range
        - Availability
        - Reviews (rating + highlights)
        - Why it fits the user’s profile (budget, convenience, family).
        """

    def run(self, state):
        if not state.get("origin") or not state.get("destination"):
            return {"error": "Origin or destination missing"}

        # DEMO MODE → stubbed transport only
        if self.mode == "Demo":
            state["transport"] = [
                {"mode": "Demo Cab", "duration": "15 min", "price_range": "$10"}
            ]
            state["utility_insights"] = ["🎬 Demo SIM info: Prepaid SIM available at airport"]
            return state

        # ONLINE MODE → Gemini API + RAG
        if self.provider == "gemini":
            api_key = os.getenv("GOOGLE_API_KEY")
            try:
                resp = requests.post(
                    "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "contents": [{
                            "parts": [{
                                "text": f"{self.prompt}\nOrigin: {state['origin']}\nDestination: {state['destination']}"
                            }]
                        }]
                    },
                    timeout=15
                )
                resp.raise_for_status()
                data = resp.json()
                output_text = data["candidates"][0]["content"]["parts"][0]["text"]
                # For now, store raw Gemini output. Later, parse into structured JSON.
                state["transport"] = [{"raw_output": output_text}]
            except Exception as e:
                print(f"⚠️ Gemini API error: {e!r}")
                state["transport"] = [{"error": "Unable to fetch transport options from Gemini"}]

        # Append SIM/Currency RAG insights
        rag_results = sim_currency_rag.query_entries(state["destination"], ["transport"], mode=self.mode)
        state["utility_insights"] = sim_currency_rag.summarize_results(rag_results, mode=self.mode)

        return state
