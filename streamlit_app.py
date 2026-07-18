import streamlit as st

# Secure API key from secrets
API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]

# Mode toggle (only Online and Demo)
mode = st.radio("Select Mode", ["Online", "Demo"])

# Helper: Google Maps Embed
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


# Reusable suggestion card
def suggestion_card(icon, title, price, rating, popularity, distance=None, duration=None, cuisine=None):
    st.markdown(f"""
    {icon} **{title}**  
    💰 Price: {price}  
    ⭐ Popularity: {popularity} (Rating: {rating})  
    {f"🚶 Distance: {distance} | ⏱️ Time: {duration}" if distance and duration else ""}  
    {f"🍴 Cuisine: {cuisine}" if cuisine else ""}
    """)

# Tabs
tab_itinerary, tab_flights, tab_hotels, tab_transport, tab_activities, tab_culinary, tab_disruptions, tab_alerts = st.tabs(
    ["Itinerary", "Flights", "Hotels", "Transport", "Activities", "Culinary", "Disruptions", "Proactive Alerts"]
)

# ---------------- ITINERARY TAB ----------------
with tab_itinerary:
    st.header("Itinerary Overview")
    st.write(f"Mode: {mode}")
    show_map("Jaipur Airport", "Jaipur Hotel")

# ---------------- FLIGHTS TAB ----------------
with tab_flights:
    st.header("Flights")
    if mode == "Demo":
        suggestion_card("✈️", "Demo Flight", "₹3000", "4.0", "🌟 Simulated")
    else:
        suggestion_card("✈️", "IndiGo 6E-330", "₹4000", "4.5", "🔥 Popular")
    show_map("Bengaluru Airport", "Jaipur Airport")

# ---------------- HOTELS TAB ----------------
with tab_hotels:
    st.header("Hotels")
    if mode == "Demo":
        suggestion_card("🏨", "Demo Hotel", "₹₹", "4.0", "🌟 Simulated")
    else:
        suggestion_card("🏨", "ITC Rajputana Jaipur", "₹₹₹", "4.5", "🔥 Popular")
    show_map("Jaipur Airport", "ITC Rajputana Jaipur")

# ---------------- TRANSPORT TAB ----------------
with tab_transport:
    st.header("Transport")
    if mode == "Demo":
        suggestion_card("🚖", "Demo Cab", "₹200", "N/A", "🌟 Simulated", distance="8 km", duration="15 min")
    else:
        suggestion_card("🚖", "Cab Service", "₹500", "N/A", "👍 Local option", distance="10 km", duration="20 min")
    show_map("ITC Rajputana Jaipur", "Amber Fort Jaipur")
    if mode == "Online":
        st.warning("⚠️ Traffic congestion detected, suggest earlier pickup.")

# ---------------- ACTIVITIES TAB ----------------
with tab_activities:
    st.header("Activities")
    itinerary_day1 = {
        "Morning": "Amber Fort Jaipur",
        "Lunch": "Laxmi Misthan Bhandar Jaipur",
        "Afternoon": "City Palace Jaipur",
        "Dinner": "Hawa Mahal Jaipur"
    }
    for slot, loc in itinerary_day1.items():
        suggestion_card("🎯", f"{slot}: {loc}", "₹₹", "4.6", "🔥 Must-see")
    show_map(itinerary_day1["Morning"], itinerary_day1["Dinner"], [itinerary_day1["Lunch"], itinerary_day1["Afternoon"]])

# ---------------- CULINARY TAB ----------------
with tab_culinary:
    st.header("Culinary")
    cuisine_filter = st.selectbox("Cuisine Preference", ["Any", "Vegetarian", "Vegan", "Street Food", "Fine Dining"])
    if mode == "Demo":
        suggestion_card("🍽️", "Demo Restaurant", "₹₹", "4.0", "🌟 Simulated", cuisine=cuisine_filter)
    else:
        suggestion_card("🍽️", "Laxmi Misthan Bhandar", "₹₹", "4.6", "🔥 Popular", distance="1.2 km", duration="5 min walk", cuisine=cuisine_filter)
    show_map("Amber Fort Jaipur", "Laxmi Misthan Bhandar Jaipur")

# ---------------- DISRUPTIONS TAB ----------------
with tab_disruptions:
    st.header("Disruption Alerts")
    if mode == "Demo":
        st.error("🚨 Demo Disruption: Flight simulated delay")
        st.success("✅ Demo Alternative Approved")
    else:
        st.error("🚨 Flight SG-112 delayed by 3 hours | ⚠️ Hotel check-in risk")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Approve Vistara UK-450"):
                st.success("✅ Approved. Itinerary updated.")
                st.info("♻️ Realignment triggered.")
        with col2:
            if st.button("Keep Original Plan"):
                st.warning("🛑 Original plan retained. Risks acknowledged.")

# ---------------- PROACTIVE ALERTS TAB ----------------
with tab_alerts:
    st.header("Proactive Alerts")
    if mode == "Demo":
        st.warning("🌦️ Demo Alert: Simulated rain forecast → Indoor activity suggested.")
    else:
        st.warning("🌦️ Rain forecast detected → Suggest indoor museum instead of outdoor walk.")
        st.warning("🚧 Road closure detected → Suggest alternate transport route.")

