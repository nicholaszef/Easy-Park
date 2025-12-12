from typing import Optional
from pydantic import BaseModel, Field

from .enums import PeranUser, StatusReservasi, StatusSlot


class ResponseUser(BaseModel):
    """User response model."""
    username: str
    role: PeranUser
    name: str


class LoginResponse(BaseModel):
    """Login response with token."""
    access_token: str
    token_type: str = "bearer"
    user: ResponseUser


class Mall(BaseModel):
    """Mall information model."""
    id: str
    name: str
    full_name: Optional[str] = None
    address: Optional[str] = None
    base_price: int
    total_slots: int
    available_slots: int


class SlotParkir(BaseModel):
    """Parking slot model."""
    id: str
    mall_id: str
    name: str
    status: StatusSlot
    location: Optional[str] = None
    slot_type: Optional[str] = "regular"


class Reservasi(BaseModel):
    """Reservation model."""
    id: str
    mall_id: str
    slot_id: str
    user_name: str
    vehicle_number: str
    phone: str
    start_time: str
    end_time: str
    duration: int
    total_price: int
    status: str
    created_at: str
    created_by: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    timestamp: int
