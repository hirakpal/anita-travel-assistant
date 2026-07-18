from pydantic import BaseModel
from typing import List, Optional

class Review(BaseModel):
    rating: Optional[float]
    highlights: List[str]

class Booking(BaseModel):
    confirmation: str
    cancellation_policy: str
    payment_options: List[str]
    reviews: Review
    status: str

class Hotel(BaseModel):
    name: str
    location: Optional[str]
    room_types: List[str]
    amenities: List[str]
    price_range: Optional[str]
    reviews: Review
    fit: Optional[str]

class Restaurant(BaseModel):
    name: str
    cuisine: Optional[str]
    dietary_options: List[str]
    seating: Optional[str]
    price_range: Optional[str]
    reviews: Review
    fit: Optional[str]

class Transport(BaseModel):
    mode: str
    duration: Optional[str]
    price_range: Optional[str]
    availability: Optional[str]
    reviews: Review
    fit: Optional[str]

class Alert(BaseModel):
    type: str
    message: str
    severity: Optional[str]  # Low, Medium, High

class Event(BaseModel):
    name: str
    date: Optional[str]
    location: Optional[str]
    description: Optional[str]
    price_range: Optional[str]
    reviews: Optional[List[str]]

class Location(BaseModel):
    name: str
    type: Optional[str]  # Landmark, Museum, Park
    opening_hours: Optional[str]
    price_range: Optional[str]
    reviews: Optional[List[str]]

class News(BaseModel):
    headline: str
    source: Optional[str]
    date: Optional[str]
    summary: Optional[str]
