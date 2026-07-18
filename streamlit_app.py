# streamlit_app.py
import streamlit as st
from orchestrator.anita import ANITA

st.title("ANITA - AI Travel Assistant")

destination = st.text_input("Enter destination:")
budget = st.selectbox("Select budget:", ["budget", "mid-range", "luxury"])
companions = st.text_input("Companions (e.g., 2 adults, 1 child)")

if st.button("Plan Trip"):
    state = {"destination": destination, "budget": budget, "companions": companions}
    anita = ANITA()
    results = anita.orchestrate(state)
    st.write("### Itinerary Suggestions")
    st.json(results)
