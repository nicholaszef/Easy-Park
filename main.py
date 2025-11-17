from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
from enum import Enum

app = FastAPI(
    title="EasyPark",
    description="API untuk sistem reservasi parkir EasyPark",
)

# Model Data
class PeranUser(str, Enum):
    USER = "user"
    ADMIN = "admin"

class LoginUser(BaseModel):
    username: str
    password: str

class ResponseUser(BaseModel):
    username: str
    role: PeranUser
    name: str

class Mall(BaseModel):
    id: str
    name: str
    full_name: str
    address: str
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
    location: str
    slot_type: str = "regular"

class RequestWaktu(BaseModel):
    start_time: str  # Format: "HH:MM"
    end_time: str    # Format: "HH:MM"

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

# Data contoh buat testing
users_db = [
    {
        "username": "user",
        "password": "12345",
        "role": PeranUser.USER,
        "name": "User"
    },
    {
        "username": "admin", 
        "password": "12345",
        "role": PeranUser.ADMIN,
        "name": "Admin"
    }
]

malls_db = [
    {
        "id": "pvj",
        "name": "PVJ",
        "full_name": "Paris Van Java",
        "address": "Jl. Sukajadi, Bandung",
        "base_price": 5000,
        "total_slots": 200,
        "available_slots": 12
    },
    {
        "id": "paskal",
        "name": "Paskal 23", 
        "full_name": "Paskal Hyper Square",
        "address": "Jl. Pasirkaliki, Bandung",
        "base_price": 5000,
        "total_slots": 150,
        "available_slots": 8
    },
    {
        "id": "sumaba",
        "name": "Sumaba",
        "full_name": "Summarecon Mall Bandung",
        "address": "Jl. Raya Kopo, Bandung",
        "base_price": 5000,
        "total_slots": 300,
        "available_slots": 15
    }
]

slots_db = {
    "pvj": [
        {"id": "pvj-1", "mall_id": "pvj", "name": "A-101", "status": StatusSlot.AVAILABLE, "location": "Lantai 2, Area A"},
        {"id": "pvj-2", "mall_id": "pvj", "name": "A-102", "status": StatusSlot.AVAILABLE, "location": "Lantai 2, Area A"},
        {"id": "pvj-3", "mall_id": "pvj", "name": "B-201", "status": StatusSlot.OCCUPIED, "location": "Lantai 2, Area B"},
        {"id": "pvj-4", "mall_id": "pvj", "name": "C-301", "status": StatusSlot.AVAILABLE, "location": "Lantai 3, Area C"},
        {"id": "pvj-5", "mall_id": "pvj", "name": "D-401", "status": StatusSlot.AVAILABLE, "location": "Lantai 4, Area D"}
    ],
    "paskal": [
        {"id": "paskal-1", "mall_id": "paskal", "name": "A-101", "status": StatusSlot.AVAILABLE, "location": "Lantai 1, Area A"},
        {"id": "paskal-2", "mall_id": "paskal", "name": "A-102", "status": StatusSlot.OCCUPIED, "location": "Lantai 1, Area A"},
        {"id": "paskal-3", "mall_id": "paskal", "name": "B-201", "status": StatusSlot.AVAILABLE, "location": "Lantai 2, Area B"},
        {"id": "paskal-4", "mall_id": "paskal", "name": "C-301", "status": StatusSlot.AVAILABLE, "location": "Lantai 3, Area C"}
    ],
    "sumaba": [
        {"id": "sumaba-1", "mall_id": "sumaba", "name": "A-101", "status": StatusSlot.AVAILABLE, "location": "Lantai 1, Area A"},
        {"id": "sumaba-2", "mall_id": "sumaba", "name": "A-102", "status": StatusSlot.AVAILABLE, "location": "Lantai 1, Area A"},
        {"id": "sumaba-3", "mall_id": "sumaba", "name": "B-201", "status": StatusSlot.OCCUPIED, "location": "Lantai 2, Area B"},
        {"id": "sumaba-4", "mall_id": "sumaba", "name": "C-301", "status": StatusSlot.AVAILABLE, "location": "Lantai 3, Area C"},
        {"id": "sumaba-5", "mall_id": "sumaba", "name": "D-401", "status": StatusSlot.AVAILABLE, "location": "Lantai 4, Area D"}
    ]
}

reservations_db = []

# Fungsi bantuan
def hitung_durasi(start_time: str, end_time: str) -> int:
    """Hitung durasi dalam jam antara dua waktu (format: HH:MM)"""
    start = datetime.strptime(start_time, "%H:%M")
    end = datetime.strptime(end_time, "%H:%M")
    durasi = (end - start).seconds // 3600
    return durasi if durasi > 0 else 24 + durasi  # Buat handle waktu lewat tengah malam

def cek_ketersediaan_waktu(mall_id: str, slot_id: str, start_time: str, end_time: str) -> bool:
    """Cek apakah slot tersedia untuk rentang waktu tertentu"""
    for reservasi in reservations_db:
        if (reservasi["slot_id"] == slot_id and 
            reservasi["status"] in ["confirmed", "active"]):
            # Cek apakah ada bentrok waktu
            waktu_mulai_sebelumnya = reservasi["start_time"]
            waktu_selesai_sebelumnya = reservasi["end_time"]
            
            # Convert ke format yang bisa dibandingin
            waktu_mulai_baru = datetime.strptime(start_time, "%H:%M")
            waktu_selesai_baru = datetime.strptime(end_time, "%H:%M")
            waktu_mulai_lama = datetime.strptime(waktu_mulai_sebelumnya, "%H:%M")
            waktu_selesai_lama = datetime.strptime(waktu_selesai_sebelumnya, "%H:%M")
            
            # Cek tabrakan waktu
            if (waktu_mulai_baru < waktu_selesai_lama and waktu_selesai_baru > waktu_mulai_lama):
                return False
    return True

def cari_mall_by_id(mall_id: str) -> Optional[dict]:
    """Cari mall berdasarkan ID"""
    for mall in malls_db:
        if mall["id"] == mall_id:
            return mall
    return None

def cari_slot_by_id(mall_id: str, slot_id: str) -> Optional[dict]:
    """Cari slot parkir berdasarkan ID"""
    if mall_id in slots_db:
        for slot in slots_db[mall_id]:
            if slot["id"] == slot_id:
                return slot
    return None

# Endpoint API
@app.get("/")
async def root():
    return {
        "message": "Selamat datang di API EasyPark",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "auth": ["POST /login"],
            "malls": ["GET /malls", "GET /malls/{mall_id}/slots"],
            "reservations": ["POST /reservations", "GET /reservations", "GET /reservations/{reservation_id}"]
        }
    }

@app.post("/login", response_model=ResponseUser)
async def login(user_data: LoginUser):
    """Endpoint buat login user dan admin"""
    for user in users_db:
        if user["username"] == user_data.username and user["password"] == user_data.password:
            return {
                "username": user["username"],
                "role": user["role"],
                "name": user["name"]
            }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Username atau password salah"
    )

@app.get("/malls", response_model=List[Mall])
async def get_malls():
    """Ambil data semua mall"""
    return malls_db

@app.get("/malls/{mall_id}")
async def get_mall(mall_id: str):
    """Ambil data mall tertentu"""
    mall = cari_mall_by_id(mall_id)
    if not mall:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mall tidak ditemukan"
        )
    return mall

@app.get("/malls/{mall_id}/slots", response_model=List[SlotParkir])
async def get_slots(mall_id: str):
    """Ambil semua slot parkir di mall tertentu"""
    if mall_id not in slots_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mall tidak ditemukan"
        )
    return slots_db[mall_id]

@app.get("/malls/{mall_id}/slots/{slot_id}")
async def get_slot(mall_id: str, slot_id: str):
    """Ambil data slot tertentu di mall"""
    slot = cari_slot_by_id(mall_id, slot_id)
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot parkir tidak ditemukan"
        )
    return slot

@app.post("/malls/{mall_id}/slots/{slot_id}/check-availability")
async def check_slot_availability(mall_id: str, slot_id: str, time_slot: RequestWaktu):
    """Cek apakah slot tersedia untuk waktu yang diminta"""
    slot = cari_slot_by_id(mall_id, slot_id)
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot parkir tidak ditemukan"
        )
    
    if slot["status"] != StatusSlot.AVAILABLE:
        return {
            "available": False,
            "message": "Slot sedang dipakai atau dalam perbaikan"
        }
    
    tersedia = cek_ketersediaan_waktu(mall_id, slot_id, time_slot.start_time, time_slot.end_time)
    
    return {
        "available": tersedia,
        "message": "Slot tersedia" if tersedia else "Slot tidak tersedia untuk waktu yang diminta"
    }

@app.post("/reservations", response_model=Reservasi)
async def create_reservation(reservation_data: RequestReservasi):
    """Buat reservasi parkir baru"""
    # Cek mall ada atau enggak
    mall = cari_mall_by_id(reservation_data.mall_id)
    if not mall:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mall tidak ditemukan"
        )
    
    # Cek slot ada atau enggak
    slot = cari_slot_by_id(reservation_data.mall_id, reservation_data.slot_id)
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot parkir tidak ditemukan"
        )
    
    # Cek slot lagi available atau enggak
    if slot["status"] != StatusSlot.AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slot tidak tersedia"
        )
    
    # Cek waktu available atau enggak
    if not cek_ketersediaan_waktu(reservation_data.mall_id, reservation_data.slot_id, 
                                 reservation_data.time_slot.start_time, reservation_data.time_slot.end_time):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slot tidak tersedia untuk waktu yang diminta"
        )
    
    # Hitung durasi dan total harga
    durasi = hitung_durasi(reservation_data.time_slot.start_time, reservation_data.time_slot.end_time)
    total_harga = mall["base_price"] * durasi
    
    # Buat reservasi baru
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
        "status": StatusReservasi.CONFIRMED,
        "created_at": datetime.now().isoformat()
    }
    
    # Update status slot jadi occupied
    for slot_item in slots_db[reservation_data.mall_id]:
        if slot_item["id"] == reservation_data.slot_id:
            slot_item["status"] = StatusSlot.OCCUPIED
            break
    
    # Update jumlah slot available di mall
    for mall_item in malls_db:
        if mall_item["id"] == reservation_data.mall_id:
            mall_item["available_slots"] -= 1
            break
    
    reservations_db.append(reservasi_baru)
    
    return reservasi_baru

@app.get("/reservations", response_model=List[Reservasi])
async def get_reservations():
    """Ambil semua data reservasi"""
    return reservations_db

@app.get("/reservations/{reservation_id}")
async def get_reservation(reservation_id: str):
    """Ambil data reservasi tertentu"""
    for reservation in reservations_db:
        if reservation["id"] == reservation_id:
            return reservation
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Reservasi tidak ditemukan"
    )

@app.put("/reservations/{reservation_id}/cancel")
async def cancel_reservation(reservation_id: str):
    """Batalin reservasi"""
    for reservation in reservations_db:
        if reservation["id"] == reservation_id:
            if reservation["status"] == StatusReservasi.CONFIRMED:
                reservation["status"] = StatusReservasi.CANCELLED
                
                # Kembalikan status slot jadi available
                for slot_item in slots_db[reservation["mall_id"]]:
                    if slot_item["id"] == reservation["slot_id"]:
                        slot_item["status"] = StatusSlot.AVAILABLE
                        break
                
                # Update jumlah slot available di mall
                for mall_item in malls_db:
                    if mall_item["id"] == reservation["mall_id"]:
                        mall_item["available_slots"] += 1
                        break
                
                return {"message": "Reservasi berhasil dibatalkan"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cuma reservasi yang masih confirmed yang bisa dibatalkan"
                )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Reservasi tidak ditemukan"
    )

@app.get("/admin/stats")
async def get_admin_stats():
    """Ambil statistik buat admin"""
    total_reservasi = len(reservations_db)
    total_pendapatan = sum(reservation["total_price"] for reservation in reservations_db)
    reservasi_aktif = len([r for r in reservations_db if r["status"] in ["confirmed", "active"]])
    
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