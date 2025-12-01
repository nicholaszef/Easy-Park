from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import math

from passlib.context import CryptContext
from jose import JWTError, jwt
from enum import Enum

# App
app = FastAPI(
    title="EasyPark",
    description="API untuk sistem reservasi parkir EasyPark",
    version="1.0.0"
)

# Enums & Models
class PeranUser(str, Enum):
    USER = "user"
    ADMIN = "admin"

class LoginIn(BaseModel):
    username: str
    password: str

class ResponseUser(BaseModel):
    username: str
    role: PeranUser
    name: str

class Mall(BaseModel):
    id: str
    name: str
    full_name: Optional[str]
    address: Optional[str]
    base_price: int
    total_slots: int
    available_slots: int

class StatusSlot(str, Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"

class SlotParkir(BaseModel):
    id: str
    mall_id: str
    name: str
    status: StatusSlot
    location: Optional[str]
    slot_type: Optional[str] = "regular"

class RequestWaktu(BaseModel):
    start_time: str  # "HH:MM"
    end_time: str    # "HH:MM"

class RequestReservasi(BaseModel):
    mall_id: str
    slot_id: str
    user_name: str
    vehicle_number: str
    phone: str
    time_slot: RequestWaktu

class Reservasi(BaseModel):
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

class StatusReservasi(str, Enum):
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# Auth config

SECRET_KEY = "ganti_dengan_secret_key_random_dan_panjang"  # Ganti sebelum production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 jam (sesuaikan)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# In-memory DB (demo)
# NOTE: passwords stored hashed
users_db = [
    {
        "username": "user",
        "hashed_password": hash_password("12345"),
        "role": PeranUser.USER.value,
        "name": "User"
    },
    {
        "username": "admin",
        "hashed_password": hash_password("12345"),
        "role": PeranUser.ADMIN.value,
        "name": "Admin"
    }
]

malls_db = [
    {"id": "pvj", "name": "PVJ", "full_name": "Paris Van Java", "address": "Jl. Sukajadi, Bandung", "base_price": 5000, "total_slots": 200, "available_slots": 12},
    {"id": "paskal", "name": "Paskal 23", "full_name": "Paskal Hyper Square", "address": "Jl. Pasirkaliki, Bandung", "base_price": 5000, "total_slots": 150, "available_slots": 8},
    {"id": "sumaba", "name": "Sumaba", "full_name": "Summarecon Mall Bandung", "address": "Jl. Raya Kopo, Bandung", "base_price": 5000, "total_slots": 300, "available_slots": 15}
]

slots_db = {
    "pvj": [
        {"id": "pvj-1", "mall_id": "pvj", "name": "A-101", "status": StatusSlot.AVAILABLE.value, "location": "Lantai 2, Area A"},
        {"id": "pvj-2", "mall_id": "pvj", "name": "A-102", "status": StatusSlot.AVAILABLE.value, "location": "Lantai 2, Area A"},
        {"id": "pvj-3", "mall_id": "pvj", "name": "B-201", "status": StatusSlot.OCCUPIED.value, "location": "Lantai 2, Area B"},
        {"id": "pvj-4", "mall_id": "pvj", "name": "C-301", "status": StatusSlot.AVAILABLE.value, "location": "Lantai 3, Area C"},
        {"id": "pvj-5", "mall_id": "pvj", "name": "D-401", "status": StatusSlot.AVAILABLE.value, "location": "Lantai 4, Area D"}
    ],
    "paskal": [
        {"id": "paskal-1", "mall_id": "paskal", "name": "A-101", "status": StatusSlot.AVAILABLE.value, "location": "Lantai 1, Area A"},
        {"id": "paskal-2", "mall_id": "paskal", "name": "A-102", "status": StatusSlot.OCCUPIED.value, "location": "Lantai 1, Area A"},
        {"id": "paskal-3", "mall_id": "paskal", "name": "B-201", "status": StatusSlot.AVAILABLE.value, "location": "Lantai 2, Area B"},
        {"id": "paskal-4", "mall_id": "paskal", "name": "C-301", "status": StatusSlot.AVAILABLE.value, "location": "Lantai 3, Area C"}
    ],
    "sumaba": [
        {"id": "sumaba-1", "mall_id": "sumaba", "name": "A-101", "status": StatusSlot.AVAILABLE.value, "location": "Lantai 1, Area A"},
        {"id": "sumaba-2", "mall_id": "sumaba", "name": "A-102", "status": StatusSlot.AVAILABLE.value, "location": "Lantai 1, Area A"},
        {"id": "sumaba-3", "mall_id": "sumaba", "name": "B-201", "status": StatusSlot.OCCUPIED.value, "location": "Lantai 2, Area B"},
        {"id": "sumaba-4", "mall_id": "sumaba", "name": "C-301", "status": StatusSlot.AVAILABLE.value, "location": "Lantai 3, Area C"},
        {"id": "sumaba-5", "mall_id": "sumaba", "name": "D-401", "status": StatusSlot.AVAILABLE.value, "location": "Lantai 4, Area D"}
    ]
}

reservations_db: List[Dict[str, Any]] = []

def time_to_minutes(t: str) -> int:
    """Konversi 'HH:MM' ke menit (0..1439), validasi format."""
    try:
        dt = datetime.strptime(t, "%H:%M")
    except ValueError:
        raise ValueError(f"Format waktu salah: '{t}'. Harus 'HH:MM'.")
    return dt.hour * 60 + dt.minute

def normalize_interval(start_min: int, end_min: int) -> (int, int):
    """Jika end <= start, tambahkan 24*60 ke end untuk handle wrap-midnight."""
    if end_min <= start_min:
        end_min += 24 * 60
    return start_min, end_min

def hitung_durasi(start_time: str, end_time: str) -> int:
    """
    Hitung durasi (jam) dengan pembulatan ke atas (ceil).
    Minimal 1 jam.
    """
    s_min = time_to_minutes(start_time)
    e_min = time_to_minutes(end_time)
    s_min, e_min = normalize_interval(s_min, e_min)
    total_minutes = e_min - s_min
    hours = math.ceil(total_minutes / 60)
    return max(1, hours)

def cek_ketersediaan_waktu(mall_id: str, slot_id: str, start_time: str, end_time: str):
    """
    Return tuple (available: bool, conflicts: List[reservation_id]).
    Overlap logic menangani wrapping midnight.
    """
    conflicts = []
    new_s = time_to_minutes(start_time)
    new_e = time_to_minutes(end_time)
    new_s, new_e = normalize_interval(new_s, new_e)

    for reservasi in reservations_db:
        if reservasi["slot_id"] != slot_id:
            continue
        if reservasi["status"] not in [StatusReservasi.CONFIRMED.value, StatusReservasi.ACTIVE.value]:
            continue

        existing_s = time_to_minutes(reservasi["start_time"])
        existing_e = time_to_minutes(reservasi["end_time"])
        existing_s, existing_e = normalize_interval(existing_s, existing_e)

        # overlap jika tidak (new_e <= existing_s or new_s >= existing_e)
        if not (new_e <= existing_s or new_s >= existing_e):
            conflicts.append(reservasi["id"])

    return (len(conflicts) == 0, conflicts)

def cari_mall_by_id(mall_id: str) -> Optional[Dict[str, Any]]:
    for mall in malls_db:
        if mall["id"] == mall_id:
            return mall
    return None

def cari_slot_by_id(mall_id: str, slot_id: str) -> Optional[Dict[str, Any]]:
    if mall_id in slots_db:
        for slot in slots_db[mall_id]:
            if slot["id"] == slot_id:
                return slot
    return None

def get_user(username: str) -> Optional[Dict[str, Any]]:
    for u in users_db:
        if u["username"] == username:
            return u
    return None

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


# Auth dependencies

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token tidak valid atau kadaluwarsa",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user(username)
    if user is None:
        raise credentials_exception
    user_copy = user.copy()
    user_copy["role"] = role
    return user_copy

def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)):
    if current_user.get("role") != PeranUser.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Akses admin diperlukan")
    return current_user

# Endpoints
@app.get("/")
async def root():
    return {
        "message": "Selamat datang di API EasyPark",
        "version": app.version,
        "docs": "/docs",
        "endpoints": {
            "auth": ["POST /login"],
            "malls": ["GET /malls", "GET /malls/{mall_id}", "GET /malls/{mall_id}/slots"],
            "reservations": ["POST /reservations", "GET /reservations", "GET /reservations/{reservation_id}", "PUT /reservations/{reservation_id}/cancel"],
            "admin": ["GET /admin/stats (admin only)"]
        }
    }

@app.post("/login")
async def login(payload: LoginIn):
    """
    Login dan kembalikan access token (JWT).
    Body: { "username": "...", "password": "..." }
    Response: { access_token, token_type, user }
    """
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Username atau password salah")

    token_data = {"sub": user["username"], "role": user["role"]}
    access_token = create_access_token(token_data)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"username": user["username"], "role": user["role"], "name": user["name"]}
    }

@app.get("/malls", response_model=List[Mall])
async def get_malls():
    return malls_db

@app.get("/malls/{mall_id}")
async def get_mall(mall_id: str):
    mall = cari_mall_by_id(mall_id)
    if not mall:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mall tidak ditemukan")
    return mall

@app.get("/malls/{mall_id}/slots", response_model=List[SlotParkir])
async def get_slots(mall_id: str):
    if mall_id not in slots_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mall tidak ditemukan")
    return slots_db[mall_id]

@app.get("/malls/{mall_id}/slots/{slot_id}")
async def get_slot(mall_id: str, slot_id: str):
    slot = cari_slot_by_id(mall_id, slot_id)
    if not slot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot parkir tidak ditemukan")
    return slot

@app.post("/malls/{mall_id}/slots/{slot_id}/check-availability")
async def check_slot_availability(mall_id: str, slot_id: str, time_slot: RequestWaktu):
    slot = cari_slot_by_id(mall_id, slot_id)
    if not slot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot parkir tidak ditemukan")

    if slot["status"] != StatusSlot.AVAILABLE.value:
        return {"available": False, "conflicts": [], "message": "Slot sedang dipakai atau dalam perbaikan"}

    try:
        tersedia, conflicts = cek_ketersediaan_waktu(mall_id, slot_id, time_slot.start_time, time_slot.end_time)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "available": tersedia,
        "conflicts": conflicts,
        "message": "Slot tersedia" if tersedia else "Slot tidak tersedia untuk waktu yang diminta"
    }

@app.post("/reservations", response_model=Reservasi, status_code=status.HTTP_201_CREATED)
async def create_reservation(reservation_data: RequestReservasi, current_user: Dict[str, Any] = Depends(get_current_user)):
    mall = cari_mall_by_id(reservation_data.mall_id)
    if not mall:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mall tidak ditemukan")

    slot = cari_slot_by_id(reservation_data.mall_id, reservation_data.slot_id)
    if not slot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot parkir tidak ditemukan")

    if slot["status"] != StatusSlot.AVAILABLE.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slot saat ini tidak tersedia")

    try:
        tersedia, conflicts = cek_ketersediaan_waktu(reservation_data.mall_id, reservation_data.slot_id,
                                                     reservation_data.time_slot.start_time, reservation_data.time_slot.end_time)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if not tersedia:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Slot bentrok: {conflicts}")

    durasi = hitung_durasi(reservation_data.time_slot.start_time, reservation_data.time_slot.end_time)
    total_harga = mall["base_price"] * durasi

    reservation_id = str(uuid.uuid4())
    reservasi_baru = {
        "id": reservation_id,
        "mall_id": reservation_data.mall_id,
        "slot_id": reservation_data.slot_id,
        "user_name": reservation_data.user_name,
        "vehicle_number": reservation_data.vehicle_number,
        "phone": reservation_data.phone,
        "start_time": reservation_data.time_slot.start_time,
        "end_time": reservation_data.time_slot.end_time,
        "duration": durasi,
        "total_price": total_harga,
        "status": StatusReservasi.CONFIRMED.value,
        "created_at": datetime.now().isoformat(),
        "created_by": current_user["username"]
    }

    # update slot status dan available count (in-memory)
    for s in slots_db[reservation_data.mall_id]:
        if s["id"] == reservation_data.slot_id:
            s["status"] = StatusSlot.OCCUPIED.value
            break
    for m in malls_db:
        if m["id"] == reservation_data.mall_id:
            m["available_slots"] = max(0, m["available_slots"] - 1)
            break

    reservations_db.append(reservasi_baru)
    return reservasi_baru

@app.get("/reservations", response_model=List[Reservasi])
async def get_reservations(current_user: Dict[str, Any] = Depends(get_current_user)):
    return reservations_db

@app.get("/reservations/{reservation_id}")
async def get_reservation(reservation_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    for reservation in reservations_db:
        if reservation["id"] == reservation_id:
            return reservation
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservasi tidak ditemukan")

@app.put("/reservations/{reservation_id}/cancel")
async def cancel_reservation(reservation_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    for reservation in reservations_db:
        if reservation["id"] == reservation_id:
            if reservation["status"] == StatusReservasi.CONFIRMED.value:
                # only owner or admin can cancel
                if reservation.get("created_by") != current_user["username"] and current_user.get("role") != PeranUser.ADMIN.value:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Hanya pemilik atau admin yang bisa membatalkan")

                reservation["status"] = StatusReservasi.CANCELLED.value
                # rollback slot status & mall available count
                for slot_item in slots_db[reservation["mall_id"]]:
                    if slot_item["id"] == reservation["slot_id"]:
                        slot_item["status"] = StatusSlot.AVAILABLE.value
                        break
                for mall_item in malls_db:
                    if mall_item["id"] == reservation["mall_id"]:
                        mall_item["available_slots"] = min(mall_item["total_slots"], mall_item["available_slots"] + 1)
                        break
                return {"message": "Reservasi berhasil dibatalkan"}
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Hanya reservasi yang masih confirmed yang bisa dibatalkan")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservasi tidak ditemukan")

@app.get("/admin/stats")
async def get_admin_stats(current_user: Dict[str, Any] = Depends(require_admin)):
    total_reservasi = len(reservations_db)
    total_pendapatan = sum(reservation["total_price"] for reservation in reservations_db)
    reservasi_aktif = len([r for r in reservations_db if r["status"] in [StatusReservasi.CONFIRMED.value, StatusReservasi.ACTIVE.value]])
    return {
        "total_reservations": total_reservasi,
        "total_revenue": total_pendapatan,
        "active_reservations": reservasi_aktif,
        "total_malls": len(malls_db),
        "total_slots": sum(len(slots) for slots in slots_db.values())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)