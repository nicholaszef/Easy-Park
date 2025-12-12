import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models.enums import StatusReservasi, StatusSlot
from ..utils.time import cek_ketersediaan_waktu, hitung_durasi


class ParkingService:
    """Service for managing parking operations."""

    def __init__(self):
        """Initialize parking service with in-memory data."""
        self.malls_db = [
            {
                "id": "pvj",
                "name": "PVJ",
                "full_name": "Paris Van Java",
                "address": "Jl. Sukajadi, Bandung",
                "base_price": 5000,
                "total_slots": 200,
                "available_slots": 12,
            },
            {
                "id": "paskal",
                "name": "Paskal 23",
                "full_name": "Paskal Hyper Square",
                "address": "Jl. Pasirkaliki, Bandung",
                "base_price": 5000,
                "total_slots": 150,
                "available_slots": 8,
            },
            {
                "id": "sumaba",
                "name": "Sumaba",
                "full_name": "Summarecon Mall Bandung",
                "address": "Jl. Raya Kopo, Bandung",
                "base_price": 5000,
                "total_slots": 300,
                "available_slots": 15,
            },
        ]

        self.slots_db = {
            "pvj": [
                {
                    "id": "pvj-1",
                    "mall_id": "pvj",
                    "name": "A-101",
                    "status": StatusSlot.AVAILABLE.value,
                    "location": "Lantai 2, Area A",
                },
                {
                    "id": "pvj-2",
                    "mall_id": "pvj",
                    "name": "A-102",
                    "status": StatusSlot.AVAILABLE.value,
                    "location": "Lantai 2, Area A",
                },
                {
                    "id": "pvj-3",
                    "mall_id": "pvj",
                    "name": "B-201",
                    "status": StatusSlot.OCCUPIED.value,
                    "location": "Lantai 2, Area B",
                },
                {
                    "id": "pvj-4",
                    "mall_id": "pvj",
                    "name": "C-301",
                    "status": StatusSlot.AVAILABLE.value,
                    "location": "Lantai 3, Area C",
                },
                {
                    "id": "pvj-5",
                    "mall_id": "pvj",
                    "name": "D-401",
                    "status": StatusSlot.AVAILABLE.value,
                    "location": "Lantai 4, Area D",
                },
            ],
            "paskal": [
                {
                    "id": "paskal-1",
                    "mall_id": "paskal",
                    "name": "A-101",
                    "status": StatusSlot.AVAILABLE.value,
                    "location": "Lantai 1, Area A",
                },
                {
                    "id": "paskal-2",
                    "mall_id": "paskal",
                    "name": "A-102",
                    "status": StatusSlot.OCCUPIED.value,
                    "location": "Lantai 1, Area A",
                },
                {
                    "id": "paskal-3",
                    "mall_id": "paskal",
                    "name": "B-201",
                    "status": StatusSlot.AVAILABLE.value,
                    "location": "Lantai 2, Area B",
                },
                {
                    "id": "paskal-4",
                    "mall_id": "paskal",
                    "name": "C-301",
                    "status": StatusSlot.AVAILABLE.value,
                    "location": "Lantai 3, Area C",
                },
            ],
            "sumaba": [
                {
                    "id": "sumaba-1",
                    "mall_id": "sumaba",
                    "name": "A-101",
                    "status": StatusSlot.AVAILABLE.value,
                    "location": "Lantai 1, Area A",
                },
                {
                    "id": "sumaba-2",
                    "mall_id": "sumaba",
                    "name": "A-102",
                    "status": StatusSlot.AVAILABLE.value,
                    "location": "Lantai 1, Area A",
                },
                {
                    "id": "sumaba-3",
                    "mall_id": "sumaba",
                    "name": "B-201",
                    "status": StatusSlot.OCCUPIED.value,
                    "location": "Lantai 2, Area B",
                },
                {
                    "id": "sumaba-4",
                    "mall_id": "sumaba",
                    "name": "C-301",
                    "status": StatusSlot.AVAILABLE.value,
                    "location": "Lantai 3, Area C",
                },
                {
                    "id": "sumaba-5",
                    "mall_id": "sumaba",
                    "name": "D-401",
                    "status": StatusSlot.AVAILABLE.value,
                    "location": "Lantai 4, Area D",
                },
            ],
        }

        self.reservations_db: List[Dict[str, Any]] = []

    def get_all_malls(self) -> List[Dict[str, Any]]:
        """Get all malls."""
        return self.malls_db

    def get_mall_by_id(self, mall_id: str) -> Optional[Dict[str, Any]]:
        """Get mall by ID."""
        for mall in self.malls_db:
            if mall["id"] == mall_id:
                return mall
        return None

    def get_slots_by_mall(self, mall_id: str) -> List[Dict[str, Any]]:
        """Get all slots for a mall."""
        return self.slots_db.get(mall_id, [])

    def get_slot_by_id(
        self, mall_id: str, slot_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get specific slot by ID."""
        if mall_id in self.slots_db:
            for slot in self.slots_db[mall_id]:
                if slot["id"] == slot_id:
                    return slot
        return None

    def check_availability(
        self, mall_id: str, slot_id: str, start_time: str, end_time: str
    ) -> tuple[bool, List[str]]:
        """Check slot availability for time period."""
        return cek_ketersediaan_waktu(
            mall_id, slot_id, start_time, end_time, self.reservations_db
        )

    def create_reservation(
        self, reservation_data: dict, username: str
    ) -> Dict[str, Any]:
        """Create a new reservation."""
        mall = self.get_mall_by_id(reservation_data["mall_id"])
        if not mall:
            raise ValueError("Mall tidak ditemukan")

        slot = self.get_slot_by_id(
            reservation_data["mall_id"], reservation_data["slot_id"]
        )
        if not slot:
            raise ValueError("Slot parkir tidak ditemukan")

        if slot["status"] != StatusSlot.AVAILABLE.value:
            raise ValueError("Slot saat ini tidak tersedia")

        # Check availability
        tersedia, conflicts = self.check_availability(
            reservation_data["mall_id"],
            reservation_data["slot_id"],
            reservation_data["time_slot"]["start_time"],
            reservation_data["time_slot"]["end_time"],
        )

        if not tersedia:
            raise ValueError(f"Slot bentrok dengan reservasi: {conflicts}")

        # Calculate duration and price
        durasi = hitung_durasi(
            reservation_data["time_slot"]["start_time"],
            reservation_data["time_slot"]["end_time"],
        )
        total_harga = mall["base_price"] * durasi

        # Create reservation
        reservation_id = str(uuid.uuid4())
        reservasi_baru = {
            "id": reservation_id,
            "mall_id": reservation_data["mall_id"],
            "slot_id": reservation_data["slot_id"],
            "user_name": reservation_data["user_name"],
            "vehicle_number": reservation_data["vehicle_number"],
            "phone": reservation_data["phone"],
            "start_time": reservation_data["time_slot"]["start_time"],
            "end_time": reservation_data["time_slot"]["end_time"],
            "duration": durasi,
            "total_price": total_harga,
            "status": StatusReservasi.CONFIRMED.value,
            "created_at": datetime.now().isoformat(),
            "created_by": username,
        }

        # Update slot status and available count
        for s in self.slots_db[reservation_data["mall_id"]]:
            if s["id"] == reservation_data["slot_id"]:
                s["status"] = StatusSlot.OCCUPIED.value
                break

        for m in self.malls_db:
            if m["id"] == reservation_data["mall_id"]:
                m["available_slots"] = max(0, m["available_slots"] - 1)
                break

        self.reservations_db.append(reservasi_baru)
        return reservasi_baru

    def get_all_reservations(self) -> List[Dict[str, Any]]:
        """Get all reservations."""
        return self.reservations_db

    def get_reservation_by_id(
        self, reservation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get reservation by ID."""
        for reservation in self.reservations_db:
            if reservation["id"] == reservation_id:
                return reservation
        return None

    def cancel_reservation(
        self, reservation_id: str, username: str, user_role: str
    ) -> Dict[str, str]:
        """Cancel a reservation."""
        reservation = self.get_reservation_by_id(reservation_id)
        if not reservation:
            raise ValueError("Reservasi tidak ditemukan")

        if reservation["status"] != StatusReservasi.CONFIRMED.value:
            raise ValueError(
                "Hanya reservasi yang masih confirmed yang bisa dibatalkan"
            )

        # Check authorization
        if reservation.get("created_by") != username and user_role != "admin":
            raise ValueError("Hanya pemilik atau admin yang bisa membatalkan")

        # Update status
        reservation["status"] = StatusReservasi.CANCELLED.value

        # Rollback slot status
        for slot_item in self.slots_db[reservation["mall_id"]]:
            if slot_item["id"] == reservation["slot_id"]:
                slot_item["status"] = StatusSlot.AVAILABLE.value
                break

        # Rollback mall available count
        for mall_item in self.malls_db:
            if mall_item["id"] == reservation["mall_id"]:
                mall_item["available_slots"] = min(
                    mall_item["total_slots"], mall_item["available_slots"] + 1
                )
                break

        return {"message": "Reservasi berhasil dibatalkan"}

    def get_admin_stats(self) -> Dict[str, Any]:
        """Get admin statistics."""
        total_reservasi = len(self.reservations_db)
        total_pendapatan = sum(
            reservation["total_price"] for reservation in self.reservations_db
        )
        reservasi_aktif = len(
            [
                r
                for r in self.reservations_db
                if r["status"]
                in [StatusReservasi.CONFIRMED.value, StatusReservasi.ACTIVE.value]
            ]
        )
        return {
            "total_reservations": total_reservasi,
            "total_revenue": total_pendapatan,
            "active_reservations": reservasi_aktif,
            "total_malls": len(self.malls_db),
            "total_slots": sum(len(slots) for slots in self.slots_db.values()),
        }

    def check_slot_availability(
        self, mall_id: str, slot_id: str, start_time: str, end_time: str
    ) -> bool:
        """Check if slot is available for given time range."""
        tersedia, _ = self.check_availability(mall_id, slot_id, start_time, end_time)
        return tersedia
