import pytest
from app.services.parking_service import ParkingService


class TestParkingService:

    # Test get all malls
    def test_get_all_malls(self, parking_service):
        malls = parking_service.get_all_malls()
        assert len(malls) == 3
        assert any(m["id"] == "pvj" for m in malls)
        assert any(m["id"] == "paskal" for m in malls)
        assert any(m["id"] == "sumaba" for m in malls)

    # Test get mall by id when exists
    def test_get_mall_by_id_exists(self, parking_service):
        mall = parking_service.get_mall_by_id("pvj")
        assert mall is not None
        assert mall["id"] == "pvj"
        assert mall["name"] == "PVJ"

    # Test get mall by id when not exists
    def test_get_mall_by_id_not_exists(self, parking_service):
        mall = parking_service.get_mall_by_id("nonexistent")
        assert mall is None

    # Test get slots by mall
    def test_get_slots_by_mall(self, parking_service):
        slots = parking_service.get_slots_by_mall("pvj")
        assert len(slots) == 5
        assert all(s["mall_id"] == "pvj" for s in slots)

    # Test get slots for non-existent mall
    def test_get_slots_by_mall_not_exists(self, parking_service):
        slots = parking_service.get_slots_by_mall("nonexistent")
        assert len(slots) == 0

    # Test get slot by id when exists
    def test_get_slot_by_id_exists(self, parking_service):
        slot = parking_service.get_slot_by_id("pvj", "pvj-1")
        assert slot is not None
        assert slot["id"] == "pvj-1"
        assert slot["mall_id"] == "pvj"

    # Test get slot by id when not exists
    def test_get_slot_by_id_not_exists(self, parking_service):
        slot = parking_service.get_slot_by_id("pvj", "nonexistent")
        assert slot is None

    # Test check availability with no conflicts
    def test_check_availability_no_conflicts(self, parking_service):
        available, conflicts = parking_service.check_availability(
            "pvj", "pvj-1", "09:00", "12:00"
        )
        assert available is True
        assert len(conflicts) == 0

    # Test create reservation success
    def test_create_reservation_success(self, parking_service):
        reservation_data = {
            "mall_id": "pvj",
            "slot_id": "pvj-1",
            "user_name": "Test User",
            "vehicle_number": "B1234XYZ",
            "phone": "08123456789",
            "time_slot": {"start_time": "09:00", "end_time": "12:00"},
        }
        reservation = parking_service.create_reservation(reservation_data, "testuser")
        assert reservation is not None
        assert reservation["mall_id"] == "pvj"
        assert reservation["slot_id"] == "pvj-1"
        assert reservation["status"] == "confirmed"
        assert reservation["duration"] == 3
        assert reservation["total_price"] == 15000

    # Test create reservation with non-existent mall
    def test_create_reservation_mall_not_found(self, parking_service):
        reservation_data = {
            "mall_id": "nonexistent",
            "slot_id": "pvj-1",
            "user_name": "Test User",
            "vehicle_number": "B1234XYZ",
            "phone": "08123456789",
            "time_slot": {"start_time": "09:00", "end_time": "12:00"},
        }
        with pytest.raises(ValueError, match="Mall tidak ditemukan"):
            parking_service.create_reservation(reservation_data, "testuser")

    # Test create reservation with non-existent slot
    def test_create_reservation_slot_not_found(self, parking_service):
        reservation_data = {
            "mall_id": "pvj",
            "slot_id": "nonexistent",
            "user_name": "Test User",
            "vehicle_number": "B1234XYZ",
            "phone": "08123456789",
            "time_slot": {"start_time": "09:00", "end_time": "12:00"},
        }
        with pytest.raises(ValueError, match="Slot parkir tidak ditemukan"):
            parking_service.create_reservation(reservation_data, "testuser")

    # Test get all reservations when empty
    def test_get_all_reservations_empty(self, parking_service):
        reservations = parking_service.get_all_reservations()
        assert len(reservations) == 0

    # Test get reservation by id when not exists
    def test_get_reservation_by_id_not_exists(self, parking_service):
        reservation = parking_service.get_reservation_by_id("nonexistent")
        assert reservation is None

    # Test cancel non-existent reservation
    def test_cancel_reservation_not_found(self, parking_service):
        with pytest.raises(ValueError, match="Reservasi tidak ditemukan"):
            parking_service.cancel_reservation("nonexistent", "user", "user")

    # Test admin stats when empty
    def test_get_admin_stats_empty(self, parking_service):
        stats = parking_service.get_admin_stats()
        assert stats["total_reservations"] == 0
        assert stats["total_revenue"] == 0
        assert stats["active_reservations"] == 0
        assert stats["total_malls"] == 3
        assert stats["total_slots"] == 14

    # Test create reservation with conflict
    def test_create_reservation_with_conflict(self, parking_service):
        reservation_data1 = {
            "mall_id": "pvj",
            "slot_id": "pvj-1",
            "user_name": "User 1",
            "vehicle_number": "B1111AAA",
            "phone": "08111111111",
            "time_slot": {"start_time": "09:00", "end_time": "11:00"},
        }
        parking_service.create_reservation(reservation_data1, "user1")

        reservation_data2 = {
            "mall_id": "pvj",
            "slot_id": "pvj-1",
            "user_name": "User 2",
            "vehicle_number": "B2222BBB",
            "phone": "08222222222",
            "time_slot": {"start_time": "10:00", "end_time": "12:00"},
        }
        with pytest.raises(ValueError, match="Slot saat ini tidak tersedia"):
            parking_service.create_reservation(reservation_data2, "user2")

    # Test check slot availability
    def test_check_slot_availability_available(self, parking_service):
        available = parking_service.check_slot_availability(
            "pvj", "pvj-2", "09:00", "11:00"
        )
        assert available is True

    # Test reservation price calculation
    def test_reservation_price_calculation(self, parking_service):
        reservation_data = {
            "mall_id": "pvj",
            "slot_id": "pvj-4",
            "user_name": "Test User",
            "vehicle_number": "B1234XYZ",
            "phone": "08123456789",
            "time_slot": {"start_time": "09:00", "end_time": "12:00"},
        }
        reservation = parking_service.create_reservation(reservation_data, "testuser")
        assert reservation["total_price"] == 15000
