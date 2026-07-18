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
        for parsed in parsed_chunks:
            try:
                booking = Booking(**parsed)
                bookings.append(booking.dict())
            except Exception as e:
                print(f"⚠️ Booking parse error: {e!r}")

    return bookings
import re

def parse_hotels_output(raw_text: str):
    hotels = []
    chunks = re.split(r"(?:Hotel|Property)[:\- ]", raw_text, flags=re.IGNORECASE)

    for chunk in chunks:
        if not chunk.strip():
            continue

        parsed = {
            "name": None,
            "location": None,
            "room_types": [],
            "amenities": [],
            "price_range": None,
            "reviews": {"rating": None, "highlights": []},
            "fit": None
        }

        name_match = re.search(r"([A-Za-z ]+)", chunk)
        if name_match:
            parsed["name"] = name_match.group(1).strip()

        loc_match = re.search(r"(near|location)[:\- ]+(.+?)(\.|\n)", chunk, re.IGNORECASE)
        if loc_match:
            parsed["location"] = loc_match.group(2).strip()

        rooms = re.findall(r"(Standard|Deluxe|Suite)", chunk, re.IGNORECASE)
        parsed["room_types"] = list(set([r.title() for r in rooms]))

        amenities = re.findall(r"(WiFi|Pool|Breakfast|Gym)", chunk, re.IGNORECASE)
        parsed["amenities"] = list(set([a.title() for a in amenities]))

        price_match = re.search(r"\$\d+–\$\d+", chunk)
        if price_match:
            parsed["price_range"] = price_match.group(0)

        rating_match = re.search(r"rating[:\- ]+([0-9]\.[0-9])", chunk, re.IGNORECASE)
        if rating_match:
            parsed["reviews"]["rating"] = float(rating_match.group(1))

        highlights = re.findall(r"(service|food|location|value|comfort)", chunk, re.IGNORECASE)
        parsed["reviews"]["highlights"] = list(set([h.capitalize() for h in highlights]))

        fit_match = re.search(r"(fit|best for)[:\- ]+(.+?)(\.|\n)", chunk, re.IGNORECASE)
        if fit_match:
            parsed["fit"] = fit_match.group(2).strip()

        hotels.append(parsed)
        for parsed in parsed_chunks:
            try:
                hotel = Hotel(**parsed)
                hotels.append(hotel.dict())
            except Exception as e:
                print(f"⚠️ Hotel parse error: {e!r}")
    return hotels

def parse_food_output(raw_text: str):
    restaurants = []
    chunks = re.split(r"(?:Restaurant|Eatery)[:\- ]", raw_text, flags=re.IGNORECASE)

    for chunk in chunks:
        if not chunk.strip():
            continue

        parsed = {
            "name": None,
            "cuisine": None,
            "dietary_options": [],
            "seating": None,
            "price_range": None,
            "reviews": {"rating": None, "highlights": []},
            "fit": None
        }

        name_match = re.search(r"([A-Za-z ]+)", chunk)
        if name_match:
            parsed["name"] = name_match.group(1).strip()

        cuisine_match = re.search(r"(cuisine|type)[:\- ]+(.+?)(\.|\n)", chunk, re.IGNORECASE)
        if cuisine_match:
            parsed["cuisine"] = cuisine_match.group(2).strip()

        dietary = re.findall(r"(Vegetarian|Vegan|Gluten-free)", chunk, re.IGNORECASE)
        parsed["dietary_options"] = list(set([d.title() for d in dietary]))

        seating_match = re.search(r"(seating|style)[:\- ]+(.+?)(\.|\n)", chunk, re.IGNORECASE)
        if seating_match:
            parsed["seating"] = seating_match.group(2).strip()

        price_match = re.search(r"\$\d+–\$\d+", chunk)
        if price_match:
            parsed["price_range"] = price_match.group(0)

        rating_match = re.search(r"rating[:\- ]+([0-9]\.[0-9])", chunk, re.IGNORECASE)
        if rating_match:
            parsed["reviews"]["rating"] = float(rating_match.group(1))

        highlights = re.findall(r"(authentic|friendly|quick service|atmosphere)", chunk, re.IGNORECASE)
        parsed["reviews"]["highlights"] = list(set([h.capitalize() for h in highlights]))

        fit_match = re.search(r"(fit|best for)[:\- ]+(.+?)(\.|\n)", chunk, re.IGNORECASE)
        if fit_match:
            parsed["fit"] = fit_match.group(2).strip()

        restaurants.append(parsed)
        for parsed in parsed_chunks:
            try:
                restaurant = Restaurant(**parsed)
                restaurants.append(restaurant.dict())
            except Exception as e:
                print(f"⚠️ Restaurant parse error: {e!r}")

    return restaurants

def parse_transport_output(raw_text: str):
    transports = []
    chunks = re.split(r"(?:Transport|Mode)[:\- ]", raw_text, flags=re.IGNORECASE)

    for chunk in chunks:
        if not chunk.strip():
            continue

        parsed = {
            "mode": None,
            "duration": None,
            "price_range": None,
            "availability": None,
            "reviews": {"rating": None, "highlights": []},
            "fit": None
        }

        mode_match = re.search(r"(Cab|Metro|Bus|Rental Car)", chunk, re.IGNORECASE)
        if mode_match:
            parsed["mode"] = mode_match.group(1).title()

        duration_match = re.search(r"(\d+ ?min|\d+ ?hours?)", chunk)
        if duration_match:
            parsed["duration"] = duration_match.group(1)

        price_match = re.search(r"\$\d+–\$\d+", chunk)
        if price_match:
            parsed["price_range"] = price_match.group(0)

        avail_match = re.search(r"(availability)[:\- ]+(.+?)(\.|\n)", chunk, re.IGNORECASE)
        if avail_match:
            parsed["availability"] = avail_match.group(2).strip()

        rating_match = re.search(r"rating[:\- ]+([0-9]\.[0-9])", chunk, re.IGNORECASE)
        if rating_match:
            parsed["reviews"]["rating"] = float(rating_match.group(1))

        highlights = re.findall(r"(reliable|comfortable|budget|fast)", chunk, re.IGNORECASE)
        parsed["reviews"]["highlights"] = list(set([h.capitalize() for h in highlights]))

        fit_match = re.search(r"(fit|best for)[:\- ]+(.+?)(\.|\n)", chunk, re.IGNORECASE)
        if fit_match:
            parsed["fit"] = fit_match.group(2).strip()

        transports.append(parsed)
        for parsed in parsed_chunks:
            try:
                transport = Transport(**parsed)
                transports.append(transport.dict())
            except Exception as e:
                print(f"⚠️ Transport parse error: {e!r}")

    return transports


