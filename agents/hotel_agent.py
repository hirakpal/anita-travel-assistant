#agents/hotel_agent.py
import os
import requests
from rag import youtube_rag
from prompts.hotel_prompt import HOTEL_PROMPT
from utils.cache import call_api
from utils.prompt_cache import build_gemini_request
from utils.parsers import parse_hotels_json_output
class HotelAgent:
    def __init__(self, name="HotelAgent", mode="Online", provider="gemini"):
        self.name = name
        self.mode = mode
        self.provider = provider
        self.prompt = HOTEL_PROMPT

    def run(self, state):
        if not state.get("destination"):
            return {"error": "Destination missing"}

        # DEMO MODE → rich stubbed hotels showcasing the full schema
        if self.mode == "Demo":
            destination = state["destination"]
            state["hotels"] = [
                {
                    "name": f"{destination} Heritage Palace",
                    "location": f"Old City, {destination}",
                    "price": "$$$", "rating": 4.7,
                    "popularity": "Demo: iconic heritage stay with royal architecture",
                    "fit": "Best for travelers wanting an immersive, luxurious heritage experience",
                    "room_type": "Heritage Suite", "bed_size": "King", "style": "Local heritage",
                    "amenities": ["WiFi", "Pool", "Spa", "Restaurant", "24/7 Security"],
                    "highlights": "Demo: hand-painted frescoes and a rooftop restaurant with panoramic views",
                    "review_summary": "Demo: guests praise the regal ambiance and attentive staff",
                    "distances": [{"landmark": "City Center", "distance": "1.0 km / 5 min drive"}],
                },
                {
                    "name": f"{destination} Family Resort", "location": f"Suburbs, {destination}",
                    "price": "$$", "rating": 4.5,
                    "popularity": "Demo: family-friendly resort with kids' activities",
                    "fit": "Best for families, including those with seniors or young children",
                    "room_type": "Family Suite", "bed_size": "King and Twin", "style": "Modern resort",
                    "amenities": ["WiFi", "Pool", "Kids Club", "Elevator", "Ground-floor rooms"],
                    "highlights": "Demo: babysitting services and a quiet, gated environment",
                    "review_summary": "Demo: praised for accessibility and child-friendly amenities",
                    "distances": [{"landmark": "Airport", "distance": "12 km / 25 min drive"}],
                },
                {
                    "name": f"{destination} Central Inn", "location": f"Downtown, {destination}",
                    "price": "$", "rating": 4.2,
                    "popularity": "Demo: budget-friendly and centrally located",
                    "fit": "Best for solo travelers and budget-conscious groups",
                    "room_type": "Standard Room", "bed_size": "Queen", "style": "Boutique",
                    "amenities": ["WiFi", "24/7 Front Desk", "Well-lit entrance"],
                    "highlights": "Demo: walking distance to major attractions, safe well-lit street",
                    "review_summary": "Demo: solo travelers note it feels safe and social",
                    "distances": [{"landmark": "Train Station", "distance": "0.5 km / 8 min walk"}],
                },
                {
                    "name": f"{destination} Eco Lodge", "location": f"Green Belt, {destination}",
                    "price": "$$", "rating": 4.4,
                    "popularity": "Demo: sustainable eco-lodge near nature trails",
                    "fit": "Best for adventure and eco-conscious travelers",
                    "room_type": "Garden Cottage", "bed_size": "Queen", "style": "Eco-friendly",
                    "amenities": ["WiFi", "Organic Restaurant", "Bike Rentals"],
                    "highlights": "Demo: solar-powered and adjacent to hiking trails",
                    "review_summary": "Demo: loved for its sustainability and peaceful setting",
                    "distances": [{"landmark": "Nature Reserve", "distance": "2.0 km / 10 min drive"}],
                },
            ]
            state["vlog_insights"] = ["🎬 Demo vlog: Hotel booking highlights", "🎬 Demo vlog: Top-rated stays walkthrough"]
            return state

        # ONLINE MODE → Gemini API
        if self.provider == "gemini":
            profile = state.get("traveler_type", "General")
            budget = state.get("budget", "Mid-range")
            travel_party = state.get("travel_party", "")
            purpose = state.get("purpose", "")
            constraint = state.get("constraint")

            def _fetch():
                api_key = os.getenv("GOOGLE_API_KEY")
                text = f"Destination: {state['destination']}\nTraveler type: {profile}\nBudget tier: {budget}"
                if travel_party:
                    text += f"\nTravel party: {travel_party}"
                if purpose:
                    text += f"\nPurpose of trip: {purpose}"
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
                params = {"destination": state["destination"], "profile": profile, "budget": budget,
                          "travel_party": travel_party, "purpose": purpose, "constraint": constraint}
                output_text = call_api("gemini:hotel", params, fetch_fn=_fetch)
                state["hotels"] = parse_hotels_json_output(output_text)
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
