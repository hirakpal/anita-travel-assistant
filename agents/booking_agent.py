class BookingAgent:
    def __init__(self, name):
        self.name = name
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
        return {
            "booking": {
                "confirmation": "Booking ID: ABC123, Dates: 12–18 Aug",
                "cancellation_policy": "Free cancellation until 72 hours before check-in",
                "payment_options": ["Credit Card", "PayPal"],
                "reviews": {
                    "rating": 4.6,
                    "highlights": [
                        "Easy booking process",
                        "Refunds handled smoothly",
                        "Secure payment options"
                    ]
                },
                "status": "Reservations confirmed for hotel, food, tours, and flights."
            }
        }

