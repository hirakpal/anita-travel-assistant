#orchestrator/anita.py
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
