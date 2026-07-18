from orchestrator.state_manager import StateManager
from agents.hotel_agent import HotelAgent
from agents.food_agent import FoodAgent
from agents.tour_agent import TourAgent
from agents.flight_agent import FlightAgent
from agents.weather_agent import WeatherAgent
from agents.booking_agent import BookingAgent
from agents.impact_assessment_agent import ImpactAssessmentAgent
from agents.news_agent import NewsAgent

class ANITA:
    def __init__(self, initial_state, mode="Online"):
        self.prompt = ANITA_PROMPT
        self.state_manager = StateManager(initial_state)
        self.mode = mode

        # Initialize agents
        self.agents = {
            "hotel": HotelAgent("HotelAgent"),
            "food": FoodAgent("FoodAgent"),
            "tour": TourAgent("TourAgent"),
            "flight": FlightAgent("FlightAgent"),
            "weather": WeatherAgent("WeatherAgent"),
            "news": NewsAgent(mode=mode.lower()),
            "impact": ImpactAssessmentAgent(mode=mode),
            "booking": BookingAgent("BookingAgent")
        }

    def orchestrate(self, traveler_type="general", preferences=None):
    results = {}

    # Step 1: Run core agents
    for name in ["hotel", "food", "tour", "flight", "weather", "news"]:
        if self.state_manager.route(name, self.routes):
            output = self.agents[name].run(self.state_manager.state)
            self.state_manager.update(name, output)
            results[name] = output

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


    
    def finalize_booking(self, itinerary, user_confirmation):
        if user_confirmation:
            return self.agents["booking"].run(itinerary)
        return {"status": "Booking not confirmed"}
