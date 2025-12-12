from enum import Enum


class PeranUser(str, Enum):
    """User role enumeration."""
    USER = "user"
    ADMIN = "admin"


class StatusSlot(str, Enum):
    """Parking slot status."""
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"


class StatusReservasi(str, Enum):
    """Reservation status."""
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
