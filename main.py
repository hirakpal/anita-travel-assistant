import sys
import streamlit as st
from orchestrator.anita import ANITA
from utils.cache import get_cache_stats
from utils.semantic_cache import get_semantic_cache_stats
from utils.prompt_cache import get_prompt_cache_stats

# Avoid UnicodeEncodeError when agents print emoji on Windows consoles (cp1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Secure API key from secrets
API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]

st.title("✈️ ANITA — Your AI Travel Concierge")

# Mode toggle (only Online and Demo)
mode = st.radio("Select Mode", ["Online", "Demo"])

# ---------------- Helper: Google Maps Embed ----------------
def show_map(origin, destination, waypoints=None):
    if mode == "Online":
        if waypoints and len(waypoints) > 0:
            wp_str = "|".join([w for w in waypoints if w])  # filter out empty strings
            maps_url = f"https://www.google.com/maps/embed/v1/directions?key={API_KEY}&origin={origin}&destination={destination}&waypoints={wp_str}"
        else:
            maps_url = f"https://www.google.com/maps/embed/v1/directions?key={API_KEY}&origin={origin}&destination={destination}"
        st.markdown(f"""
            <iframe width="100%" height="400" frameborder="0" style="border:0"
            src="{maps_url}" allowfullscreen></iframe>
        """, unsafe_allow_html=True)
    elif mode == "Demo":
        st.success(f"🎬 Demo Mode: Simulated route {origin} → {destination} with waypoints {waypoints}")

# ---------------- Helper: Suggestion Card ----------------
def suggestion_card(icon, title, price, rating, popularity, distance=None, duration=None, cuisine=None):
    st.markdown(f"""
    {icon} **{title}**
    💰 Price: {price}
    ⭐ Popularity: {popularity} (Rating: {rating})
    {f"🚶 Distance: {distance} | ⏱️ Time: {duration}" if distance and duration else ""}
    {f"🍴 Cuisine: {cuisine}" if cuisine else ""}
    """)

# ---------------- Session state: conversation + ANITA instance ----------------
if "anita" not in st.session_state or st.session_state.get("mode") != mode:
    st.session_state.anita = ANITA({}, mode=mode)
    st.session_state.mode = mode
    st.session_state.messages = []
    st.session_state.results = None

    greeting, _ready = st.session_state.anita.chat("", [])
    st.session_state.messages.append({"role": "assistant", "content": greeting})

if st.button("🔄 Start Over"):
    st.session_state.anita = ANITA({}, mode=mode)
    st.session_state.messages = []
    st.session_state.results = None
    greeting, _ready = st.session_state.anita.chat("", [])
    st.session_state.messages.append({"role": "assistant", "content": greeting})
    st.rerun()

anita = st.session_state.anita
trip = anita.state_manager.state

# ---------------- Chat with Anita ----------------
st.subheader("💬 Chat with Anita")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_message = st.chat_input("Tell Anita about your trip...")
if user_message:
    st.session_state.messages.append({"role": "user", "content": user_message})
    history = st.session_state.messages[:-1]  # everything before this new user turn

    reply, ready = anita.chat(user_message, history)
    st.session_state.messages.append({"role": "assistant", "content": reply})

    if ready and st.session_state.results is None:
        with st.spinner("Building your itinerary — coordinating with Hotel, Food, Tour, Flight, Weather, Transport, and News agents..."):
            st.session_state.results = anita.orchestrate(traveler_type=trip.get("traveler_type", "general"))

    st.rerun()

results = st.session_state.results

# ---------------- Itinerary tabs (shown once Anita has enough info) ----------------
if results is None:
    st.info("Chat with Anita above to plan your trip — once she has your origin, destination, and dates, your itinerary will appear here.")
else:
    tab_itinerary, tab_flights, tab_hotels, tab_transport, tab_activities, tab_culinary, tab_disruptions, tab_alerts = st.tabs(
        ["Itinerary", "Flights", "Hotels", "Transport", "Activities", "Culinary", "Disruptions", "Proactive Alerts"]
    )

    # ---------------- ITINERARY TAB ----------------
    with tab_itinerary:
        st.header("Itinerary Overview")
        st.write(f"Mode: {mode}")
        st.write(f"**Trip:** {trip.get('origin')} → {trip.get('destination')} ({trip.get('dates')})")
        st.write(f"**Budget:** {trip.get('budget')} | **Food preference:** {trip.get('food_pref')}")

        st.subheader("Caching & Token Savings")

        st.caption("Fragment cache — per tool-call (Gemini/API) caching")
        fragment_stats = get_cache_stats()
        col1, col2, col3 = st.columns(3)
        col1.metric("Cache Hits", fragment_stats["hits"])
        col2.metric("Cache Misses", fragment_stats["misses"])
        col3.metric("Token Savings", f"{fragment_stats['savings_percent']}%")

        st.caption("Semantic cache — whole-request dedup at the orchestrator level")
        semantic_stats = get_semantic_cache_stats()
        col4, col5, col6 = st.columns(3)
        col4.metric("Semantic Hits", semantic_stats["hits"])
        col5.metric("Semantic Misses", semantic_stats["misses"])
        col6.metric("Pipeline Runs Saved", f"{semantic_stats['savings_percent']}%")

        st.caption("Prompt cache — static system-prompt handle reuse")
        prompt_stats = get_prompt_cache_stats()
        col7, col8, col9 = st.columns(3)
        col7.metric("Handle Reuses", prompt_stats["handle_reuses"])
        col8.metric("Handles Created", prompt_stats["handles_created"])
        col9.metric("Reuse Rate", f"{prompt_stats['reuse_percent']}%")

        show_map(trip.get("origin"), trip.get("destination"))

    # ---------------- FLIGHTS TAB ----------------
    with tab_flights:
        st.header("Flights")
        flights = results.get("flight", {}).get("flights", [])
        if flights:
            for f in flights:
                suggestion_card("✈️", f.get("airline", "Unknown"), f.get("price_range", "N/A"),
                                f.get("reviews", {}).get("rating", "N/A"),
                                f.get("constraint_applied", ""))
        show_map(trip.get("origin"), trip.get("destination"))

    # ---------------- HOTELS TAB ----------------
    with tab_hotels:
        st.header("Hotels")
        hotels = results.get("hotel", {}).get("hotels", [])
        if hotels:
            for h in hotels:
                suggestion_card("🏨", h.get("name", "Unknown"), h.get("price", "N/A"),
                                h.get("rating", "N/A"), h.get("popularity", ""))
        show_map(trip.get("destination"), hotels[0].get("name", trip.get("destination")) if hotels else trip.get("destination"))

    # ---------------- TRANSPORT TAB ----------------
    with tab_transport:
        st.header("Transport")
        transport = results.get("transport", {}).get("transport", [])
        if transport:
            for t in transport:
                suggestion_card("🚖", t.get("name", "Transport"), t.get("price", "N/A"),
                                t.get("rating", "N/A"), t.get("popularity", ""),
                                distance=t.get("distance"), duration=t.get("duration"))
        show_map(trip.get("origin"), trip.get("destination"))

    # ---------------- ACTIVITIES TAB ----------------
    with tab_activities:
        st.header("Activities")
        tours = results.get("tour", {}).get("tour_summary", {}).get("tours", [])
        if tours:
            for t in tours:
                suggestion_card("🎯", t.get("title", "Activity"), t.get("price", "N/A"),
                                t.get("rating", "N/A"), t.get("popularity", "🔥 Popular"))
        if tours:
            show_map(tours[0].get("location", trip.get("destination")), tours[-1].get("location", trip.get("destination")))

    # ---------------- CULINARY TAB ----------------
    with tab_culinary:
        st.header("Culinary")
        cuisine_filter = st.selectbox("Cuisine Preference", ["Any", "Vegetarian", "Vegan", "Street Food", "Fine Dining"])
        foods = results.get("food", {}).get("restaurants", [])
        if foods:
            for f in foods:
                suggestion_card("🍽️", f.get("name", "Restaurant"), f.get("price", "N/A"),
                                f.get("rating", "N/A"), f.get("popularity", ""),
                                distance=f.get("distance"), duration=f.get("duration"), cuisine=cuisine_filter)
        show_map(trip.get("destination"), foods[0].get("name", trip.get("destination")) if foods else trip.get("destination"))

    # ---------------- DISRUPTIONS TAB ----------------
    with tab_disruptions:
        st.header("Disruption Alerts")
        alerts = results.get("impact_assessment", {}).get("risk", {})
        if mode == "Demo":
            st.error("🚨 Demo Disruption: Flight simulated delay")
            st.success("✅ Demo Alternative Approved")
        else:
            if alerts.get("risk_level") == "High":
                st.error("🚨 High risk detected in itinerary")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Approve Alternate Plan"):
                        st.success("✅ Approved. Itinerary updated.")
                        st.info("♻️ Realignment triggered.")
                with col2:
                    if st.button("Keep Original Plan"):
                        st.warning("🛑 Original plan retained. Risks acknowledged.")
            else:
                st.success(f"✅ No major risks detected (risk level: {alerts.get('risk_level', 'Unknown')}).")
                if alerts.get("weather"):
                    st.write(f"🌦️ Weather: {alerts['weather']}")
                if alerts.get("political"):
                    st.write(f"🏛️ Political/local: {alerts['political']}")

    # ---------------- PROACTIVE ALERTS TAB ----------------
    with tab_alerts:
        st.header("Proactive Alerts")
        if mode == "Demo":
            st.warning("🌦️ Demo Alert: Simulated rain forecast → Indoor activity suggested.")
        else:
            weather = results.get("weather", {})
            forecast_text = str(weather.get("forecast", ""))
            advisories_text = str(weather.get("advisories", ""))

            shown_alert = False
            if "rain" in forecast_text.lower() or "rain" in advisories_text.lower():
                st.warning("🌦️ Rain forecast detected → Suggest indoor museum instead of outdoor walk.")
                shown_alert = True
            if weather.get("advisories") and weather["advisories"] != "No major advisories":
                st.info(f"ℹ️ {weather['advisories']}")
                shown_alert = True

            if not shown_alert:
                st.success("✅ No proactive alerts right now — conditions look normal for your trip.")
