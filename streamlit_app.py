import streamlit as st
from orchestrator.anita import ANITA

st.title("ANITA - AI Travel Assistant")

destination = st.text_input("Enter destination:")
origin = st.text_input("Enter origin (for flights):")
budget = st.selectbox("Select budget:", ["budget", "mid-range", "luxury"])
companions = st.text_input("Companions (e.g., 2 adults, 1 child)")
food_pref = st.text_input("Food preference (e.g., vegetarian, vegan)")
dates = st.text_input("Travel dates (e.g., 12–18 Aug)")

if st.button("Plan Trip"):
    state = {
        "destination": destination,
        "origin": origin,
        "budget": budget,
        "companions": companions,
        "food_pref": food_pref,
        "dates": dates
    }
    anita = ANITA(state)
    results = anita.orchestrate()

    st.write("### Itinerary Suggestions")
    st.json(results)

    st.write("### Agent Interaction Trace")
    for agent, output in results.items():
        st.markdown(f"**{agent.capitalize()} Agent ran successfully**")
        st.json(output)

