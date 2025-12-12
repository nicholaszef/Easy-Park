from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    """Login request model."""
    username: str = Field(..., min_length=1, description="Username")
    password: str = Field(..., min_length=1, description="Password")


class RequestWaktu(BaseModel):
    """Time slot request."""
    start_time: str = Field(..., pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$", description="Start time in HH:MM format")
    end_time: str = Field(..., pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$", description="End time in HH:MM format")


class RequestReservasi(BaseModel):
    """Reservation request model."""
    mall_id: str = Field(..., min_length=1, description="Mall identifier")
    slot_id: str = Field(..., min_length=1, description="Parking slot identifier")
    user_name: str = Field(..., min_length=1, description="User name")
    vehicle_number: str = Field(..., min_length=1, description="Vehicle registration number")
    phone: str = Field(..., min_length=10, description="Phone number")
    time_slot: RequestWaktu = Field(..., description="Reservation time slot")
