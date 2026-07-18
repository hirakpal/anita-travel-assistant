class BookingAgent:
    def __init__(self, name="BookingAgent", mode="Online"):
        self.name = name
        self.mode = mode
        self.prompt = """
        You are the Booking Agent.
        Task: Given confirmed hotels, tours, and flights, finalize reservations.
        Include:
        - Booking confirmation details (reference number, dates)
        - Cancellation policies (flexible, non-refundable, refund timelines)
        - Payment options (credit card, PayPal, cash at property)
        - Traveler reviews (rating + highlights like 'easy booking process')
        - Adjust itinerary if changes occur (weather reroute, flight rebooking).
        Return a summary of confirmed reservations.
        """

    def run(self, state):
        if self.mode == "Demo":
            return {
                "booking": {
                    "confirmation": "Booking ID: DEMO123, Dates: 12–18 Aug",
                    "cancellation_policy": "Demo: Free cancellation until 72 hours",
                    "payment_options": ["Credit Card", "PayPal"],
                    "reviews": {
                        "rating": 4.5,
                        "highlights": ["Demo booking process smooth", "Refunds handled"]
                    },
                    "status": "Demo reservations confirmed for hotel, tours, flights."
                }
            }

        # Online mode: build bookings from state
        bookings = []
        if "hotels" in state:
            for h in state["hotels"]:
                bookings.append({
                    "type": "hotel",
                    "name": h.get("name"),
                    "confirmation": f"HotelRef-{h.get('name','HOTEL')[:3].upper()}123",
                    "dates": state.get("dates", "N/A"),
                    "cancellation_policy": "Free cancellation until 48 hours before check-in",
                    "payment_options": ["Credit Card", "Cash at property"],
                    "reviews": {"rating": 4.4, "highlights": ["Easy booking", "Good support"]},
                    "status": "Hotel reservation confirmed"
                })

        if "flights" in state:
            for f in state["flights"]:
                bookings.append({
                    "type": "flight",
                    "airline": f.get("airline"),
                    "confirmation": f"FlightRef-{f.get('airline','FLIGHT')[:3].upper()}456",
                    "dates": state.get("dates", "N/A"),
                    "cancellation_policy": "Non-refundable after ticket issuance",
                    "payment_options": ["Credit Card", "UPI"],
                    "reviews": {"rating": 4.2, "highlights": ["Smooth booking", "Secure payment"]},
                    "status": "Flight reservation confirmed"
                })

        if "activities" in state:
            for a in state["activities"].values():
                bookings.append({
                    "type": "activity",
                    "name": a.get("name"),
                    "confirmation": f"ActRef-{a.get('name','ACT')[:3].upper()}789",
                    "dates": state.get("dates", "N/A"),
                    "cancellation_policy": "Refundable up to 24 hours before activity",
                    "payment_options": ["Credit Card", "PayPal"],
                    "reviews": {"rating": 4.6, "highlights": ["Easy booking", "Flexible cancellation"]},
                    "status": "Activity reservation confirmed"
                })

        return {"booking": bookings}
