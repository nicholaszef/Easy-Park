
import logging
from contextlib import asynccontextmanager
from typing import Any, List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    LoginIn,
    LoginResponse,
    Mall,
    RequestReservasi,
    RequestWaktu,
    Reservasi,
    ResponseUser,
    SlotParkir,
)
from .models.response import HealthResponse
from .services.auth_service import AuthService
from .services.parking_service import ParkingService
from .utils.auth import create_access_token, get_current_user, oauth2_scheme, require_admin
from .utils.timestamp import get_current_timestamp

# Logger setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global services
auth_service: AuthService | None = None
parking_service: ParkingService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for service initialization."""
    global auth_service, parking_service
    auth_service = AuthService()
    parking_service = ParkingService()
    logger.info("EasyPark services initialized")
    yield
    logger.info("Shutting down EasyPark services")


# FastAPI app
app = FastAPI(
    title="EasyPark",
    description="API untuk sistem reservasi parkir EasyPark",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_auth_service() -> AuthService:
    """Dependency to get auth service."""
    if auth_service is None:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return auth_service


def get_parking_service() -> ParkingService:
    """Dependency to get parking service."""
    if parking_service is None:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return parking_service


def get_current_user_dependency(
    token: str = Depends(oauth2_scheme),
    auth_svc: AuthService = Depends(get_auth_service),
):
    """Get current user with proper dependency injection."""
    return get_current_user(token, auth_svc.get_all_users())


@app.get("/")
async def root():
    """Root endpoint with API overview."""
    return {
        "message": "Selamat datang di API EasyPark",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "auth": ["POST /login"],
            "malls": [
                "GET /malls",
                "GET /malls/{mall_id}",
                "GET /malls/{mall_id}/slots",
            ],
            "reservations": [
                "POST /reservations",
                "GET /reservations",
                "GET /reservations/{reservation_id}",
                "PUT /reservations/{reservation_id}/cancel",
            ],
            "admin": ["GET /admin/stats (admin only)"],
        },
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": get_current_timestamp(),
    }


@app.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginIn, auth_svc: AuthService = Depends(get_auth_service)
):
    """Login endpoint - returns JWT token."""
    user = auth_svc.authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah",
        )

    token_data = {"sub": user["username"], "role": user["role"]}
    access_token = create_access_token(token_data)

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=ResponseUser(
            username=user["username"], role=user["role"], name=user["name"]
        ),
    )


@app.get("/malls", response_model=List[Mall])
async def get_malls(svc: ParkingService = Depends(get_parking_service)):
    """Get all malls."""
    return svc.get_all_malls()


@app.get("/malls/{mall_id}")
async def get_mall(
    mall_id: str, svc: ParkingService = Depends(get_parking_service)
):
    """Get mall by ID."""
    mall = svc.get_mall_by_id(mall_id)
    if not mall:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Mall tidak ditemukan"
        )
    return mall


@app.get("/malls/{mall_id}/slots", response_model=List[SlotParkir])
async def get_slots(
    mall_id: str, svc: ParkingService = Depends(get_parking_service)
):
    """Get all parking slots for a mall."""
    slots = svc.get_slots_by_mall(mall_id)
    if not slots:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Mall tidak ditemukan"
        )
    return slots


@app.get("/malls/{mall_id}/slots/{slot_id}")
async def get_slot(
    mall_id: str,
    slot_id: str,
    svc: ParkingService = Depends(get_parking_service),
):
    """Get specific parking slot."""
    slot = svc.get_slot_by_id(mall_id, slot_id)
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot parkir tidak ditemukan",
        )
    return slot


@app.post("/malls/{mall_id}/slots/{slot_id}/check-availability")
async def check_slot_availability(
    mall_id: str,
    slot_id: str,
    time_slot: RequestWaktu,
    svc: ParkingService = Depends(get_parking_service),
):
    """Check parking slot availability for a time period."""
    slot = svc.get_slot_by_id(mall_id, slot_id)
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot parkir tidak ditemukan",
        )

    if slot["status"] != "available":
        return {
            "available": False,
            "conflicts": [],
            "message": "Slot sedang dipakai atau dalam perbaikan",
        }

    try:
        tersedia, conflicts = svc.check_availability(
            mall_id, slot_id, time_slot.start_time, time_slot.end_time
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "available": tersedia,
        "conflicts": conflicts,
        "message": "Slot tersedia" if tersedia else "Slot tidak tersedia untuk waktu yang diminta",
    }


@app.post(
    "/reservations", response_model=Reservasi, status_code=status.HTTP_201_CREATED
)
async def create_reservation(
    reservation_data: RequestReservasi,
    current_user: dict = Depends(get_current_user_dependency),
    svc: ParkingService = Depends(get_parking_service),
):
    """Create a new parking reservation."""
    try:
        reservation = svc.create_reservation(
            reservation_data.model_dump(), current_user["username"]
        )
        return reservation
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating reservation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@app.get("/reservations", response_model=List[Reservasi])
async def get_reservations(
    current_user: dict = Depends(get_current_user_dependency),
    svc: ParkingService = Depends(get_parking_service),
):
    """Get all reservations."""
    return svc.get_all_reservations()


@app.get("/reservations/{reservation_id}")
async def get_reservation(
    reservation_id: str,
    current_user: dict = Depends(get_current_user_dependency),
    svc: ParkingService = Depends(get_parking_service),
):
    """Get reservation by ID."""
    reservation = svc.get_reservation_by_id(reservation_id)
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservasi tidak ditemukan",
        )
    return reservation


@app.put("/reservations/{reservation_id}/cancel")
async def cancel_reservation(
    reservation_id: str,
    current_user: dict = Depends(get_current_user_dependency),
    svc: ParkingService = Depends(get_parking_service),
):
    """Cancel a reservation."""
    try:
        result = svc.cancel_reservation(
            reservation_id, current_user["username"], current_user["role"]
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error cancelling reservation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@app.get("/admin/stats")
async def get_admin_stats(
    current_user: dict = Depends(get_current_user_dependency),
    svc: ParkingService = Depends(get_parking_service),
):
    """Get admin statistics (admin only)."""
    require_admin(current_user)
    return svc.get_admin_stats()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
