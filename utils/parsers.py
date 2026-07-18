import re

def parse_booking_output(raw_text: str):
    """
    Parse Gemini free-text booking output into structured JSON.
    Supports multiple bookings by splitting on 'Booking ID' or 'Reservation'.
    """

    bookings = []
    # Split raw text into chunks per booking
    chunks = re.split(r"(?:Booking ID|Reservation)[:\- ]", raw_text, flags=re.IGNORECASE)

    for chunk in chunks:
        if not chunk.strip():
            continue

        parsed = {
            "confirmation": None,
            "cancellation_policy": None,
            "payment_options": [],
            "reviews": {"rating": None, "highlights": []},
            "status": None
        }

        # Confirmation
        conf_match = re.search(r"([A-Z0-9]{3,})", chunk)
        if conf_match:
            parsed["confirmation"] = conf_match.group(1)

        # Cancellation policy
        cancel_match = re.search(r"(cancellation policy|cancellation)[:\- ]+(.+?)(\.|\n)", chunk, re.IGNORECASE)
        if cancel_match:
            parsed["cancellation_policy"] = cancel_match.group(2).strip()

        # Payment options
        payments = re.findall(r"(Credit Card|PayPal|Cash|UPI)", chunk, re.IGNORECASE)
        if payments:
            parsed["payment_options"] = list(set([p.title() for p in payments]))

        # Reviews
        rating_match = re.search(r"rating[:\- ]+([0-9]\.[0-9])", chunk, re.IGNORECASE)
        if rating_match:
            parsed["reviews"]["rating"] = float(rating_match.group(1))

        highlights = re.findall(r"(easy booking|refund|support|smooth|secure payment)", chunk, re.IGNORECASE)
        if highlights:
            parsed["reviews"]["highlights"] = list(set([h.capitalize() for h in highlights]))

        # Status
        if "confirmed" in chunk.lower() or "reservation" in chunk.lower():
            parsed["status"] = "Reservation confirmed"

        bookings.append(parsed)

    return bookings
