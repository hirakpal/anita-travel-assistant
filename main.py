import pytest
from orchestrator.anita import ANITA
from agents.hotel_agent import HotelAgent
from agents.food_agent import FoodAgent
from agents.tour_agent import TourAgent
from agents.flight_agent import FlightAgent
from utils.cache import call_api, savings_percent
from utils.token_tracker import log_tokens
from rag.youtube_rag import filter_videos

# ----------------------------
# Agent Output Validation
# ----------------------------

def test_hotel_agent_output():
    agent = HotelAgent("HotelAgent")
    state = {"destination": "Rome"}
    result = agent.run(state)
    assert "hotels" in result
    assert isinstance(result["hotels"], list)

def test_food_agent_output():
    agent = FoodAgent("FoodAgent")
    state = {"destination": "Rome", "food_pref": "vegetarian"}
    result = agent.run(state)
    assert "food" in result
    assert isinstance(result["food"], list)

def test_tour_agent_output():
    agent = TourAgent("TourAgent")
    state = {"destination": "Rome"}
    result = agent.run(state)
    assert "tours" in result
    assert isinstance(result["tours"], list)

def test_flight_agent_output():
    agent = FlightAgent("FlightAgent")
    state = {"origin": "Delhi", "destination": "Rome"}
    result = agent.run(state)
    assert "flights" in result
    assert isinstance(result["flights"], list)

# ----------------------------
# Orchestration Logic
# ----------------------------

def test_anita_orchestration():
    anita = ANITA()
    state = {"destination": "Rome", "budget": "mid-range"}
    results = anita.orchestrate(state)
    assert "hotel" in results
    assert "food" in results
    assert "tour" in results
    assert "flight" in results

# ----------------------------
# Resilience & Error Handling
# ----------------------------

def test_missing_destination():
    agent = HotelAgent("HotelAgent")
    state = {}
    result = agent.run(state)
    assert "error" in result

def test_api_fallback():
    response = call_api("google_maps", {"origin":"Rome","dest":"Vatican"})
    cached_response = call_api("google_maps", {"origin":"Rome","dest":"Vatican"})  # cache hit
    assert response == cached_response

# ----------------------------
# RAG Pipeline
# ----------------------------

def test_youtube_rag_filter():
    videos = [
        {"id":"1","views":60000,"upload_date":"2026-06-01"},
        {"id":"2","views":40000,"upload_date":"2026-06-01"}
    ]
    filtered = filter_videos(videos)
    assert len(filtered) == 1
    assert filtered[0]["id"] == "1"

# ----------------------------
# Efficiency Tracking
# ----------------------------

def test_token_logging():
    tracker = {"tokens_used": 0}
    log_tokens(100, 50, tracker)
    assert tracker["tokens_used"] >= 150

def test_cache_savings():
    call_api("maps", {"origin":"Rome","dest":"Vatican"})
    call_api("maps", {"origin":"Rome","dest":"Vatican"})  # cache hit
    assert savings_percent() > 0
