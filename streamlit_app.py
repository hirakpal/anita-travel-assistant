import streamlit as st
import plotly.express as px

# Toggle between live and demo mode
mode = st.radio("Mode", ["Live 🔴", "Demo 🟢"])

# Mock responses for demo mode
mock_data = {
    "pre_trip": {
        "event": "Rome airport strike planned on 15 Aug",
        "alert": "Flight AI-202 may be disrupted",
        "suggestion": "Switch to Flight AI-204 on 16 Aug"
    },
    "ongoing_trip": {
        "event": "Trastevere street festival tonight at 6 PM",
        "alert": "Road closure near Trastevere after 5 PM",
        "suggestion": "Move dinner to Piazza Navona and add festival visit"
    }
}

def run_event_agent(location, date):
    if mode == "Demo 🟢":
        return mock_data["ongoing_trip"]["event"]
    else:
        # Replace with Google Events API call
        return f"Live events fetched for {location} on {date}"

def run_alert_agent(location):
    if mode == "Demo 🟢":
        return mock_data["ongoing_trip"]["alert"]
    else:
        # Replace with live disruption API call
        return f"Live alerts fetched for {location}"

def run_tour_agent(location, date):
    event = run_event_agent(location, date)
    alert = run_alert_agent(location)
    if mode == "Demo 🟢":
        return mock_data["ongoing_trip"]["suggestion"]
    else:
        return f"Tour plan adjusted based on {event} and {alert}"

# UI rendering
st.title("ANITA Timeline Tracker")

st.markdown("### 📍 Location → 🎉 Event → 🚨 Alert → 🏛️ Tour")

event = run_event_agent("Rome", "13 July 2026")
alert = run_alert_agent("Rome")
suggestion = run_tour_agent("Rome", "13 July 2026")

st.info(f"Event: {event}")
st.warning(f"Alert: {alert}")

# Approval workflow card
st.markdown("### Suggested Change")
st.write(f"Original Plan: Dinner at Trastevere, 7 PM")
st.write(f"Suggested Plan: {suggestion}")

col1, col2 = st.columns(2)
if col1.button("✅ Approve Change"):
    st.success("Change approved — itinerary updated ✔")
if col2.button("❌ Keep Original Plan"):
    st.error("Original plan retained ✖")

# Travel DNA Radar Chart
travel_dna = {
    "Budget": 6,
    "Hotel Style": 7,
    "Food Preference": 8,
    "Tour Type": 7,
    "Flight Comfort": 6,
    "Weather Tolerance": 5,
    "Transport Preference": 6,
    "Event Engagement": 8 if mode == "Demo 🟢" else 5
}

df = px.data.wind()  # placeholder
df = px.line_polar(
    pd.DataFrame(dict(r=list(travel_dna.values()), theta=list(travel_dna.keys()))),
    r='r', theta='theta', line_close=True
)
df.update_traces(fill='toself')
st.plotly_chart(df)
