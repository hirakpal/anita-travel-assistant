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
            if self.state_manager.route(name):
                output = self.agents[name].run(self.state_manager.state)
                self.state_manager.update(name, output)
                results[name] = output

                # Weather disruption → rerun TourAgent
                if name == "weather" and "advisories" in output.get("weather", {}):
                    if "storm" in output["weather"]["advisories"].lower():
                        alt_tours = self.agents["tour"].run(self.state_manager.state)
                        self.state_manager.update("tour", alt_tours)
                        results["tour"] = alt_tours

        # Step 2: Assess impact
        impact_report = self.agents["impact"].assess(results, traveler_type, preferences)
        results["impact_assessment"] = impact_report.dict()

        # Step 3: Generate alternates based on impact findings
        alternates = {}
        if "hotel" in impact_report.alternates:
            alternates["hotels"] = self.agents["hotel"].run({**self.state_manager.state, "constraint": "budget"})
        if "transport" in impact_report.alternates:
            alternates["transport"] = self.agents["flight"].run({**self.state_manager.state, "constraint": "safe"})
        if "tour" in impact_report.alternates:
            alternates["tours"] = self.agents["tour"].run({**self.state_manager.state, "constraint": "accessible"})
        results["alternate_options"] = alternates

        return results

    def finalize_booking(self, itinerary, user_confirmation):
        if user_confirmation:
            return self.agents["booking"].run(itinerary)
        return {"status": "Booking not confirmed"}
