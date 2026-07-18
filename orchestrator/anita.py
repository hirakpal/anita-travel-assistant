from agents.hotel_agent import HotelAgent
from agents.food_agent import FoodAgent
from agents.tour_agent import TourAgent
from agents.flight_agent import FlightAgent

class ANITA:
    def __init__(self):
        self.agents = {
            "hotel": HotelAgent("HotelAgent"),
            "food": FoodAgent("FoodAgent"),
            "tour": TourAgent("TourAgent"),
            "flight": FlightAgent("FlightAgent")
        }

    def orchestrate(self, state):
        results = {}
        for key, agent in self.agents.items():
            results[key] = agent.run(state)
        return results
