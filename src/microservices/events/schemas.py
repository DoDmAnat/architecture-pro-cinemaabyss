from datetime import datetime

from pydantic import BaseModel, Field


class Event(BaseModel):
    id: str
    type: str
    timestamp: datetime
    payload: dict


class MovieEvent(BaseModel):
    movie_id: int
    title: str
    action: str
    user_id: int | None = None
    rating: float | None = None
    genres: list[str] | None = None
    description: str | None = None


class UserEvent(BaseModel):
    user_id: int
    action: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    username: str | None = None
    email: str | None = None


class PaymentEvent(BaseModel):
    payment_id: int
    user_id: int
    amount: float
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    method_type: str | None = None


class EventResponse(BaseModel):
    status: str
    partition: int
    offset: int
    event: Event
