#orchestrator/anita.py
import os
import re
import requests
import concurrent.futures
from prompts.anita_prompt import ANITA_PROMPT
from prompts.itinerary_prompt import ITINERARY_PROMPT
from prompts.guide_prompt import VISA_PROMPT, SIM_CURRENCY_PROMPT, LOCAL_TIPS_PROMPT, VIDEO_SUMMARY_PROMPT
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
from utils.cache import call_api
from utils.prompt_cache import build_gemini_request
from rag import visa_rag
from rag import youtube_rag
from rag.youtube_ingest import ingest_destination_videos
from utils.parsers import extract_json_object
from utils.audit_trail import log_step

# Mandatory trip details gathered conversationally, in the order Anita asks
# for them. Nothing is "ready" until all of these are known.
MANDATORY_CHAT_SLOTS = [
    ("origin", "Where are you traveling from?"),
    ("destination", "Great — and where would you like to go?"),
    ("dates", "What dates are you traveling (or how many days)?"),
    ("purpose", "What's the purpose of this trip — leisure, business, a honeymoon, pilgrimage, adventure?"),
    ("travel_party", "Who's traveling — just you, or with family? Any seniors or infants/young children in the group?"),
]

# Secondary details — only asked once every mandatory slot above is filled.
OPTIONAL_CHAT_SLOTS = [
    ("budget", "What's your budget tier — Budget, Mid-range, or Luxury?"),
    ("food_pref", "Any food preferences? (e.g. vegetarian, vegan, or just 'Any')"),
]

CHAT_SLOTS = MANDATORY_CHAT_SLOTS + OPTIONAL_CHAT_SLOTS


def _infer_traveler_type(travel_party: str) -> str:
    """Best-effort classification of free-text travel_party into the enum
    downstream agents/impact-assessment expect. Used by the rule-based chat
    fallback where there's no Gemini available to do this inference."""
    text = (travel_party or "").lower()
    if any(w in text for w in ["infant", "baby", "toddler", "young child", "kid"]):
        return "family_with_infant"
    if any(w in text for w in ["senior", "elderly", "old age"]):
        return "senior"
    if "solo" in text and any(w in text for w in ["female", "woman", "girl"]):
        return "solo_female"
    if "solo" in text or "alone" in text or "myself" in text:
        return "solo"
    if "family" in text:
        return "family"
    if any(w in text for w in ["adventure", "trek", "hike"]):
        return "adventure"
    return "general"

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
            if k in ("origin", "destination", "dates", "purpose", "travel_party", "budget", "food_pref", "traveler_type") and v
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
            self.state_manager.state.get(k) for k in ("origin", "destination", "dates", "purpose", "travel_party")
        )
        return reply, ready

    def _chat_rule_based(self, message: str):
        """
        Deterministic slot-filling used in Demo mode, and as the fallback
        when the Gemini chat call fails in Online mode — asks one mandatory
        question at a time (origin, destination, dates, purpose, travel
        party), then the optional ones, no network/API key required.
        """
        state = self.state_manager.state
        message = (message or "").strip()

        pending_slot = next((slot for slot, _ in CHAT_SLOTS if not state.get(slot)), None)
        if pending_slot and message:
            state[pending_slot] = message
            if pending_slot == "travel_party":
                state["traveler_type"] = _infer_traveler_type(message)

        next_slot = next(((slot, question) for slot, question in CHAT_SLOTS if not state.get(slot)), None)
        if next_slot:
            return next_slot[1], False

        state.setdefault("traveler_type", "general")
        return "Perfect, I have everything I need! Building your itinerary now...", True

    def _guess_duration_days(self):
        dates_text = str(self.state_manager.state.get("dates") or "")
        match = re.search(r"(\d+)\s*(?:day|days)\b", dates_text, re.IGNORECASE)
        if match:
            return max(1, min(int(match.group(1)), 14))
        match = re.search(r"(\d+)\s*(?:night|nights)\b", dates_text, re.IGNORECASE)
        if match:
            return max(1, min(int(match.group(1)) + 1, 14))
        return 3

    def _build_timeline(self, results):
        """
        Arrange the actual hotel/food/tour/transport options already chosen
        by the sub-agents into a day-by-day schedule. Never invents new
        options — only sequences the real ones.
        """
        hotels = [h.get("name") for h in results.get("hotel", {}).get("hotels", []) if h.get("name")]
        foods = [f.get("name") for f in results.get("food", {}).get("restaurants", []) if f.get("name")]
        tours = [t.get("title") for t in results.get("tour", {}).get("tour_summary", {}).get("tours", []) if t.get("title")]
        duration = self._guess_duration_days()

        return self.rebuild_timeline_from_selection(hotels, foods, tours)

    def rebuild_timeline_from_selection(self, hotels, foods, tours):
        """
        Public entry point for re-sequencing the timeline after the user
        adds/removes specific hotel, restaurant, or activity options — only
        ever arranges the given names, never invents new ones.
        """
        duration = self._guess_duration_days()
        if self.mode != "Demo" and (hotels or foods or tours):
            try:
                return self._timeline_gemini(hotels, foods, tours, duration)
            except Exception as e:
                print(f"⚠️ Timeline build error: {e!r}")
        return self._timeline_rule_based(hotels, foods, tours, duration)

    def _timeline_gemini(self, hotels, foods, tours, duration):
        destination = self.state_manager.state.get("destination", "")

        def _fetch():
            api_key = os.getenv("GOOGLE_API_KEY")
            dynamic_text = (
                f"Destination: {destination}\n"
                f"Trip length: {duration} days\n"
                f"Hotel options: {hotels}\n"
                f"Restaurant options: {foods}\n"
                f"Tour/activity options: {tours}\n"
            )
            body = build_gemini_request("ANITA:timeline", ITINERARY_PROMPT, dynamic_text)
            resp = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent",
                params={"key": api_key},
                json=body,
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

        params = {"destination": destination, "duration": duration, "hotels": hotels, "foods": foods, "tours": tours}
        text = call_api("gemini:timeline", params, fetch_fn=_fetch)
        obj = extract_json_object(text)
        timeline = (obj or {}).get("timeline")
        if not timeline:
            return self._timeline_rule_based(hotels, foods, tours, duration)
        return timeline

    def _timeline_rule_based(self, hotels, foods, tours, duration):
        """Deterministic day-by-day layout used in Demo mode / as a Gemini fallback."""
        hotel = hotels[0] if hotels else "your hotel"
        timeline = []
        for day in range(1, duration + 1):
            schedule = []
            if day == 1:
                schedule.append({"time": "Morning", "activity": f"Arrival and check-in at {hotel}"})
            if tours:
                schedule.append({"time": "Afternoon", "activity": tours[(day - 1) % len(tours)]})
            if foods:
                schedule.append({"time": "Evening", "activity": f"Dinner at {foods[(day - 1) % len(foods)]}"})
            if day == duration and duration > 1:
                schedule.append({"time": "Late", "activity": f"Check-out from {hotel} and departure"})
            timeline.append({"day": day, "label": "Arrival Day" if day == 1 else ("Departure Day" if day == duration else ""), "schedule": schedule})
        return timeline

    def _build_guide(self, results):
        """
        Traveler Guide: visa requirements, SIM/currency info, local tips, and
        a rollup of YouTube-vlog highlights already gathered by other agents.

        The RAG/Pinecone lookups (visa, SIM/currency) only return real data
        once someone has actually indexed content for this destination —
        nothing in this codebase seeds that data yet, so in practice they
        come back empty. Rather than show a broken-looking blank tab,
        visa/SIM/tips each fall back to a direct Gemini call (in Demo mode
        or on any failure, they fall back further to canned demo text).

        video_highlights is a genuine cross-video synthesis: instead of
        listing each vlog's raw quote separately (which just reads like a
        pile of disconnected snippets), we pull every indexed video's
        transcript excerpt for this destination and hand ALL of them to one
        Gemini call that merges overlapping points by theme.
        """
        destination = self.state_manager.state.get("destination", "")

        try:
            visa_results = visa_rag.query_requirements(destination, mode=self.mode)
            visa_info = visa_rag.summarize_results(visa_results, mode=self.mode)
        except Exception as e:
            print(f"⚠️ Visa RAG error: {e!r}")
            visa_info = []

        sim_currency_info = results.get("transport", {}).get("utility_insights", [])

        try:
            video_matches = youtube_rag.get_video_transcripts(destination, top_k=8, mode=self.mode)
        except Exception as e:
            print(f"⚠️ Video transcript fetch error: {e!r}")
            video_matches = []

        # Local tips always needs a Gemini call; visa/SIM only need one if
        # their RAG lookup came back empty; video summary only if we found
        # transcripts to synthesize. Run whichever are needed concurrently
        # instead of one-at-a-time.
        fallback_tasks = {"local_tips": (LOCAL_TIPS_PROMPT, "tips")}
        if not visa_info:
            fallback_tasks["visa"] = (VISA_PROMPT, "visa_info")
        if not sim_currency_info:
            fallback_tasks["sim_currency"] = (SIM_CURRENCY_PROMPT, "sim_currency_info")

        fallback_results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(fallback_tasks) + 1) as executor:
            futures = {
                executor.submit(self._guide_gemini_fallback, prompt, response_key, destination): name
                for name, (prompt, response_key) in fallback_tasks.items()
            }
            video_future = executor.submit(self._summarize_video_transcripts, video_matches, destination)
            for future in concurrent.futures.as_completed(futures):
                fallback_results[futures[future]] = future.result()
            video_summary = video_future.result()

        visa_info = fallback_results.get("visa", visa_info)
        sim_currency_info = fallback_results.get("sim_currency", sim_currency_info)
        local_tips = fallback_results["local_tips"]

        return {
            "visa": visa_info,
            "sim_currency": sim_currency_info,
            "local_tips": local_tips,
            "video_highlights": {
                "summary": video_summary,
                "sources": [{"title": v["title"], "creator": v["creator"]} for v in video_matches],
            },
        }

    def _summarize_video_transcripts(self, video_matches, destination):
        """Turn several videos' transcript excerpts into one synthesized summary (see _build_guide)."""
        if not video_matches:
            return []
        if self.mode == "Demo":
            return [f"Demo: synthesized video summary for {destination}"]

        transcripts_block = "\n\n".join(
            f"--- Video: \"{v['title']}\" by {v['creator']} ---\n{v['excerpt']}"
            for v in video_matches
        )
        try:
            def _fetch():
                api_key = os.getenv("GOOGLE_API_KEY")
                body = build_gemini_request(
                    "ANITA:guide:video_summary", VIDEO_SUMMARY_PROMPT,
                    f"Destination: {destination}\n\n{transcripts_block}"
                )
                resp = requests.post(
                    "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent",
                    params={"key": api_key},
                    json=body,
                    timeout=25
                )
                resp.raise_for_status()
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]

            cache_key = {"destination": destination, "video_ids": sorted(v["title"] for v in video_matches)}
            text = call_api("gemini:guide:video_summary", cache_key, fetch_fn=_fetch)
            obj = extract_json_object(text)
            return (obj or {}).get("video_summary", []) or []
        except Exception as e:
            print(f"⚠️ Video summary error: {e!r}")
            return []

    def _guide_gemini_fallback(self, prompt, response_key, destination):
        if self.mode == "Demo":
            return [f"Demo: {response_key.replace('_', ' ')} highlight for {destination}"]
        try:
            def _fetch():
                api_key = os.getenv("GOOGLE_API_KEY")
                body = build_gemini_request(f"ANITA:guide:{response_key}", prompt, f"Destination: {destination}")
                resp = requests.post(
                    "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent",
                    params={"key": api_key},
                    json=body,
                    timeout=15
                )
                resp.raise_for_status()
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]

            text = call_api(f"gemini:guide:{response_key}", {"destination": destination}, fetch_fn=_fetch)
            obj = extract_json_object(text)
            return (obj or {}).get(response_key, []) or []
        except Exception as e:
            print(f"⚠️ Guide fallback error ({response_key}): {e!r}")
            return []

    def _ensure_video_content(self, destination):
        """
        Index real travel-vlog transcripts for this destination (via
        SearchAPI.io) the first time it's ever requested, so every agent's
        query_videos() call this run — and the Guide tab's video rollup —
        has genuine content to find instead of an empty Pinecone index.
        Cached forever (ttl=None) per destination so we never re-ingest.
        """
        if self.mode == "Demo" or not destination:
            return

        def _do_ingest():
            try:
                count = ingest_destination_videos(destination)
                print(f"📹 Indexed {count} travel videos for {destination}")
            except Exception as e:
                print(f"⚠️ Video ingestion error: {e!r}")
            return {"done": True}

        try:
            call_api(f"youtube_ingest:{destination}", {"destination": destination}, fetch_fn=_do_ingest, ttl=None)
        except Exception as e:
            print(f"⚠️ Video ingestion cache error: {e!r}")

    def _run_pipeline(self, traveler_type="general", preferences=None):
        results = {}

        # Step 1: Run core agents concurrently — they're independent of each
        # other, and each gets its own shallow copy of the input state (agents
        # mutate-and-return their argument in place, so sharing one dict
        # across threads would race on shared keys like "vlog_insights").
        # Video ingestion runs alongside them rather than blocking first.
        agent_names = [name for name in ["hotel", "food", "tour", "flight", "weather", "transport", "news"]
                        if self.state_manager.route(name, self.routes)]
        base_state = dict(self.state_manager.state)

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(agent_names) + 1) as executor:
            ingest_future = executor.submit(self._ensure_video_content, base_state.get("destination"))
            agent_futures = {
                executor.submit(self.agents[name].run, dict(base_state)): name
                for name in agent_names
            }

            for future in concurrent.futures.as_completed(agent_futures):
                name = agent_futures[future]
                try:
                    output = future.result()
                    has_error = isinstance(output, dict) and "error" in output
                    log_step(f"agent:{name}", "error" if has_error else "success",
                              detail=output.get("error") if has_error else None)
                except Exception as e:
                    log_step(f"agent:{name}", "error", error=e)
                    output = {"error": str(e)}
                # Shallow snapshot: the agent already operated on its own
                # isolated state copy, but snapshot anyway for consistency
                # with the rest of the pipeline (e.g. json-serializability).
                snapshot = dict(output) if isinstance(output, dict) else output
                self.state_manager.update(name, snapshot)
                results[name] = snapshot

            try:
                ingest_future.result()  # ensure indexing finishes before the Guide step reads it
                log_step("video_ingestion", "success")
            except Exception as e:
                log_step("video_ingestion", "error", error=e)

        # Step 2: Assess impact
        log_step("impact_assessment", "start")
        try:
            impact_report = self.agents["impact"].assess(results, traveler_type, preferences)
            results["impact_assessment"] = impact_report.dict()
            log_step("impact_assessment", "success")
        except Exception as e:
            log_step("impact_assessment", "error", error=e)
            raise

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

        # Step 3.5: Build a day-by-day timeline from the real options above
        log_step("timeline_build", "start")
        try:
            results["timeline"] = self._build_timeline(results)
            log_step("timeline_build", "success")
        except Exception as e:
            log_step("timeline_build", "error", error=e)
            raise

        # Step 3.6: Build the traveler Guide (Visa, SIM/currency, video highlights)
        log_step("guide_build", "start")
        try:
            results["guide"] = self._build_guide(results)
            log_step("guide_build", "success")
        except Exception as e:
            log_step("guide_build", "error", error=e)
            raise

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

    def orchestrate(self, traveler_type="general", preferences=None):
        # Outer-layer semantic cache: a near-duplicate request (same trip,
        # slightly reworded preferences) skips the entire multi-agent run.
        state = self.state_manager.state
        query_text = (
            f"origin={state.get('origin')} destination={state.get('destination')} "
            f"dates={state.get('dates')} purpose={state.get('purpose')} "
            f"travel_party={state.get('travel_party')} budget={state.get('budget')} "
            f"food_pref={state.get('food_pref')} traveler_type={traveler_type} "
            f"preferences={preferences} mode={self.mode}"
        )
        log_step("orchestrate", "start", detail=f"destination={state.get('destination')} mode={self.mode}")
        try:
            result = semantic_call(query_text, lambda: self._run_pipeline(traveler_type, preferences), threshold=0.95)
            log_step("orchestrate", "success")
            return result
        except Exception as e:
            log_step("orchestrate", "error", error=e)
            raise

    def revise_itinerary(self, feedback: str, traveler_type="general", preferences=None):
        """
        Human-in-the-loop revision: re-run the pipeline with the user's
        rejection feedback applied as a constraint on every agent, bypassing
        the semantic cache (a revision must never be served from the
        original, now-rejected, cached itinerary).
        """
        self.state_manager.state["constraint"] = feedback
        try:
            return self._run_pipeline(traveler_type, preferences)
        finally:
            self.state_manager.state.pop("constraint", None)

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
