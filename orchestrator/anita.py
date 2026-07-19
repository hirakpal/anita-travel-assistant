#orchestrator/anita.py
import os
import requests
from prompts.anita_prompt import ANITA_PROMPT
from orchestrator.state_manager import StateManager
from agents.hotel_agent import HotelAgent
from agents.food_agent import FoodAgent
from agents.tour_agent import TourAgent
from agents.flight_agent import FlightAgent
from agents.weather_agent import WeatherAgent
from agents.transport_agent import TransportAgent
from agents.booking_agent import BookingAgent
from agents.impact_assessment_agent import ImpactAssessmentAgent
from agents.news_agent import NewsAgent
from human_agent_integration import HumanAgentIntegration
from utils.semantic_cache import semantic_call
from utils.prompt_cache import build_gemini_request
from utils.parsers import extract_json_object

# Trip details gathered conversationally, in the order Anita asks for them.
CHAT_SLOTS = [
    ("origin", "Where are you traveling from?"),
    ("destination", "Great — and where would you like to go?"),
    ("dates", "What dates are you traveling (or how many days)?"),
    ("budget", "What's your budget tier — Budget, Mid-range, or Luxury?"),
    ("food_pref", "Any food preferences? (e.g. vegetarian, vegan, or just 'Any')"),
]

class ANITA:
    def __init__(self, initial_state, mode="Online"):
        self.prompt = ANITA_PROMPT
        self.state_manager = StateManager(initial_state)
        self.mode = mode

        # Initialize agents
        self.agents = {
            "hotel": HotelAgent("HotelAgent", mode=mode),
            "food": FoodAgent("FoodAgent", mode=mode),
            "tour": TourAgent("TourAgent", mode=mode),
            "flight": FlightAgent("FlightAgent", mode=mode),
            "weather": WeatherAgent("WeatherAgent", mode=mode),
            "transport": TransportAgent("TransportAgent", mode=mode),
            "news": NewsAgent(mode=mode),
            "impact": ImpactAssessmentAgent(mode=mode),
            "booking": BookingAgent("BookingAgent", mode=mode)
        }

        # TODO: define self.routes (RouteManager or similar)
        self.routes = None

    def chat(self, message: str, history=None):
        """
        One conversational turn with Anita. Extracted trip details (origin,
        destination, dates, budget, food_pref) are merged straight into
        self.state_manager.state as they're learned.

        Returns (reply_text, ready): ready=True once enough trip info has
        been gathered to call orchestrate().
        """
        if self.mode != "Demo":
            try:
                return self._chat_gemini(message, history or [])
            except Exception as e:
                print(f"⚠️ Anita chat error: {e!r}")
        return self._chat_rule_based(message)

    def _chat_gemini(self, message: str, history):
        api_key = os.getenv("GOOGLE_API_KEY")
        known = {
            k: v for k, v in self.state_manager.state.items()
            if k in ("origin", "destination", "dates", "budget", "food_pref", "traveler_type") and v
        }
        convo = "\n".join(f"{turn['role'].capitalize()}: {turn['content']}" for turn in history)
        dynamic_text = (
            f"Trip details confirmed so far: {known}\n\n"
            f"Conversation so far:\n{convo}\n"
            f"User: {message}"
        )
        body = build_gemini_request("ANITA", self.prompt, dynamic_text)
        resp = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent",
            params={"key": api_key},
            json=body,
            timeout=15
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]

        obj = extract_json_object(text)
        if obj is None:
            # Gemini didn't return JSON — show it as the reply, but we
            # can't extract structured fields from it, so keep gathering.
            return text, False

        for key, value in (obj.get("trip_info") or {}).items():
            if value:
                self.state_manager.state[key] = value

        reply = obj.get("reply") or text
        ready = bool(obj.get("ready", False)) and all(
            self.state_manager.state.get(k) for k in ("origin", "destination", "dates")
        )
        return reply, ready

    def _chat_rule_based(self, message: str):
        """
        Deterministic slot-filling used in Demo mode, and as the fallback
        when the Gemini chat call fails in Online mode — asks one question
        at a time, no network/API key required.
        """
        state = self.state_manager.state
        message = (message or "").strip()

        pending_slot = next((slot for slot, _ in CHAT_SLOTS if not state.get(slot)), None)
        if pending_slot and message:
            state[pending_slot] = message

        next_slot = next(((slot, question) for slot, question in CHAT_SLOTS if not state.get(slot)), None)
        if next_slot:
            return next_slot[1], False

        state.setdefault("traveler_type", "general")
        return "Perfect, I have everything I need! Building your itinerary now...", True

    def orchestrate(self, traveler_type="general", preferences=None):
        def _run():
            results = {}

            # Step 1: Run core agents
            for name in ["hotel", "food", "tour", "flight", "weather", "transport", "news"]:
                if self.state_manager.route(name, self.routes):
                    output = self.agents[name].run(self.state_manager.state)
                    # Agents mutate and return the same shared state dict, so take a
                    # shallow snapshot before storing it under this agent's key —
                    # otherwise state[name] = output aliases state back into itself
                    # (state["transport"] = state) for any agent whose internal field
                    # name matches its orchestrator key (transport, weather, news).
                    snapshot = dict(output) if isinstance(output, dict) else output
                    self.state_manager.update(name, snapshot)
                    results[name] = snapshot

            # Step 2: Assess impact
            impact_report = self.agents["impact"].assess(results, traveler_type, preferences)
            results["impact_assessment"] = impact_report.dict()

            # Step 3: Build narrative
            narrative = []
            if impact_report.budget["flag"] == "Expensive":
                narrative.append("Your hotel choice looks expensive, so I’ve pulled budget alternatives.")
            if impact_report.accessibility.get("wheelchair_friendly_hotels"):
                narrative.append("Accessibility is flagged — I’ve added wheelchair‑friendly hotel and tour options.")
            if impact_report.risk["risk_level"] == "High":
                narrative.append("Risk level is high — I suggest safer transport routes or daytime flights.")
            if impact_report.sustainability["carbon_score"] == "High":
                narrative.append("This itinerary has a high carbon footprint — eco‑friendly hotels and metro transport are available.")

            results["impact_narrative"] = " ".join(narrative) if narrative else "Your itinerary looks balanced and well‑suited."

            # Step 4: Apply alternates into state
            if self.routes:
                alternates = self.routes.alternate_routes(impact_report.dict(), self.state_manager.state)
                self.state_manager.apply_alternates(alternates)

                # Step 5: Re‑query agents with constraints
                alternate_outputs = {}
                for agent_name, constraint in alternates.items():
                    alt_output = self.agents[agent_name].run(
                        {**self.state_manager.state, "constraint": constraint}
                    )
                    alternate_outputs[agent_name] = alt_output
                    self.state_manager.update(f"{agent_name}_alternates", alt_output)

                results["alternate_options"] = alternate_outputs

            return results

        # Outer-layer semantic cache: a near-duplicate request (same trip,
        # slightly reworded preferences) skips the entire multi-agent run.
        state = self.state_manager.state
        query_text = (
            f"origin={state.get('origin')} destination={state.get('destination')} "
            f"dates={state.get('dates')} budget={state.get('budget')} "
            f"food_pref={state.get('food_pref')} traveler_type={traveler_type} "
            f"preferences={preferences} mode={self.mode}"
        )
        return semantic_call(query_text, _run, threshold=0.95)

    def run_itinerary(self, state):
        flight_agent = FlightAgent(mode="Online")
        tour_agent = TourAgent(mode="Online")
        human_integration = HumanAgentIntegration()

        # Collect agent outputs
        state = flight_agent.run(state)
        tours = tour_agent.run(state)

        # Present to human
        human_integration.present_options({
            "Flights": state.get("flights", []),
            "Tours": tours.get("tour_summary", {}).get("tours", [])
        })

        # Collect feedback
        feedback = human_integration.collect_feedback()

        # Apply feedback and re‑run agents
        state = human_integration.apply_feedback(state, feedback)
        state = flight_agent.run(state)  # re‑run with constraint
        tours = tour_agent.run(state)

        return {"flights": state["flights"], "tours": tours["tour_summary"]["tours"]}

    def finalize_booking(self, itinerary, user_confirmation):
        if user_confirmation:
            return self.agents["booking"].run(itinerary)
        return {"status": "Booking not confirmed"}
