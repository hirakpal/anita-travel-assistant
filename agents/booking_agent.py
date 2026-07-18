class BookingAgent:
    def __init__(self, name):
        self.name = name
        self.prompt = """
        You are the Booking Agent.
        Task: Given confirmed hotels, tours, and flights, adjust itinerary and budget.
        - If changes occur (weather reroute, flight rebooking), update bookings accordingly.
        - Return a summary of confirmed reservations.
        """

    def run(self, state):
        return {"booking": "Reservations confirmed for hotel, food, tours, and flights."}
