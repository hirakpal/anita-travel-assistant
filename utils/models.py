from pydantic import BaseModel
from typing import List, Optional, Union

class Review(BaseModel):
    rating: Optional[float] = None
    highlights: List[str] = []

class Booking(BaseModel):
    confirmation: str
    cancellation_policy: str
    payment_options: List[str] = []
    reviews: Review = Review()
    status: str

class Hotel(BaseModel):
    name: str
    location: Optional[str] = None
    room_types: List[str] = []
    amenities: List[str] = []
    price_range: Optional[str] = None
    reviews: Review = Review()
    fit: Optional[str] = None

class Restaurant(BaseModel):
    name: str
    cuisine: Optional[str] = None
    dietary_options: List[str] = []
    seating: Optional[str] = None
    price_range: Optional[str] = None
    reviews: Review = Review()
    fit: Optional[str] = None

class Transport(BaseModel):
    mode: str
    duration: Optional[str] = None
    price_range: Optional[str] = None
    availability: Optional[str] = None
    reviews: Review = Review()
    fit: Optional[str] = None

class Alert(BaseModel):
    type: str
    message: str
    severity: Optional[str] = None  # Low, Medium, High

class Event(BaseModel):
    name: str
    date: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    price_range: Optional[str] = None
    reviews: Optional[Union[str, List[str]]] = None

class Location(BaseModel):
    name: str
    type: Optional[str] = None  # Landmark, Museum, Park
    opening_hours: Optional[str] = None
    price_range: Optional[str] = None
    reviews: Optional[Union[str, List[str]]] = None

class News(BaseModel):
    headline: str
    source: Optional[str] = None
    date: Optional[str] = None
    summary: Optional[str] = None
