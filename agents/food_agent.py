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

        # DEMO MODE → rich stubbed restaurants showcasing the full schema
        if self.mode == "Demo":
            destination = state["destination"]
            state["restaurants"] = [
                {
                    "name": f"{destination} Heritage Kitchen", "cuisine": "Local Traditional",
                    "price": "$$", "rating": 4.6, "popularity": "Demo: iconic local heritage dining",
                    "distance": "0.8 km", "duration": "10 min walk",
                    "fit": "Great for families and cultural immersion seekers",
                    "specialties": ["Signature Thali", "Local Sweets"], "ambiance": "Traditional, bustling",
                    "dietary_options": ["Vegetarian", "Vegan options"],
                    "review_summary": "Demo: diners love the authentic flavors and lively atmosphere",
                },
                {
                    "name": f"{destination} Rooftop Bistro", "cuisine": "Multi-cuisine",
                    "price": "$$$", "rating": 4.5, "popularity": "Demo: scenic rooftop dining",
                    "distance": "1.5 km", "duration": "5 min drive",
                    "fit": "Great for couples and travelers wanting a relaxed evening",
                    "specialties": ["Grilled Platter", "Signature Cocktails"], "ambiance": "Rooftop, romantic",
                    "dietary_options": ["Vegetarian", "Gluten-free"],
                    "review_summary": "Demo: praised for the view and attentive service",
                },
                {
                    "name": f"{destination} Street Food Corner", "cuisine": "Street Food",
                    "price": "$", "rating": 4.3, "popularity": "Demo: bustling street food hub",
                    "distance": "0.3 km", "duration": "5 min walk",
                    "fit": "Great for solo/adventure travelers wanting authentic bites",
                    "specialties": ["Local Chaat", "Fresh Juices"], "ambiance": "Casual, street-side, well-lit",
                    "dietary_options": ["Vegetarian"],
                    "review_summary": "Demo: solo travelers note it's busy, safe, and delicious",
                },
                {
                    "name": f"{destination} Family Diner", "cuisine": "Comfort Food",
                    "price": "$$", "rating": 4.4, "popularity": "Demo: relaxed family-friendly diner",
                    "distance": "1.0 km", "duration": "15 min walk",
                    "fit": "Great for families with seniors or young children",
                    "specialties": ["Kids Combo", "Soft-serve Desserts"], "ambiance": "Casual, spacious, quiet corners",
                    "dietary_options": ["Vegetarian", "Vegan", "Kids menu"],
                    "review_summary": "Demo: families appreciate the high chairs and quick service",
                },
            ]
            state["vlog_insights"] = ["🎬 Demo vlog: Street food highlights", "🎬 Demo vlog: Best local eats guide"]
            return state

        # ONLINE MODE → Gemini API
        if self.provider == "gemini":
            preferences = state.get("food_pref", "General")
            traveler_type = state.get("traveler_type", "General")
            travel_party = state.get("travel_party", "")
            constraint = state.get("constraint")

            def _fetch():
                api_key = os.getenv("GOOGLE_API_KEY")
                text = f"Destination: {state['destination']}\nFood preferences: {preferences}\nTraveler type: {traveler_type}"
                if travel_party:
                    text += f"\nTravel party: {travel_party}"
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
                # Identical inputs → served from cache, no Gemini tokens spent
                params = {"destination": state["destination"], "preferences": preferences, "traveler_type": traveler_type,
                          "travel_party": travel_party, "constraint": constraint}
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
