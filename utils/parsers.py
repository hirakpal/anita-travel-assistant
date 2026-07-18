import re

def parse_booking_output(raw_text: str):
    """
    Parse Gemini free-text booking output into structured JSON.
    Extracts confirmation, cancellation_policy, payment_options, reviews, and status.
    """

    parsed = {
        "confirmation": None,
        "cancellation_policy": None,
        "payment_options": [],
        "reviews": {"rating": None, "highlights": []},
        "status": None
    }

    # Confirmation
    conf_match = re.search(r"(Booking ID|Confirmation|Ref)[:\- ]+([A-Z0-9]+)", raw_text, re.IGNORECASE)
    if conf_match:
        parsed["confirmation"] = conf_match.group(2)

    # Cancellation policy
    cancel_match = re.search(r"(cancellation policy|cancellation)[:\- ]+(.+?)(\.|\n)", raw_text, re.IGNORECASE)
    if cancel_match:
        parsed["cancellation_policy"] = cancel_match.group(2).strip()

    # Payment options
    payments = re.findall(r"(Credit Card|PayPal|Cash|UPI)", raw_text, re.IGNORECASE)
    if payments:
        parsed["payment_options"] = list(set([p.title() for p in payments]))

    # Reviews (rating + highlights)
    rating_match = re.search(r"rating[:\- ]+([0-9]\.[0-9])", raw_text, re.IGNORECASE)
    if rating_match:
        parsed["reviews"]["rating"] = float(rating_match.group(1))

    highlights = re.findall(r"(easy booking|refund|support|smooth|secure payment)", raw_text, re.IGNORECASE)
    if highlights:
        parsed["reviews"]["highlights"] = list(set([h.capitalize() for h in highlights]))

    # Status
    if "confirmed" in raw_text.lower() or "reservation" in raw_text.lower():
        parsed["status"] = "Reservation confirmed"

    return parsed
