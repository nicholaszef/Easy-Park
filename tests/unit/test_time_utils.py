import pytest
from app.utils.time import (
    cek_ketersediaan_waktu,
    hitung_durasi,
    normalize_interval,
    time_to_minutes,
)


class TestTimeUtilities:

    # Test time to minutes conversion
    def test_time_to_minutes_valid(self):
        assert time_to_minutes("00:00") == 0
        assert time_to_minutes("01:00") == 60
        assert time_to_minutes("12:30") == 750
        assert time_to_minutes("23:59") == 1439

    # Test time to minutes with invalid input
    def test_time_to_minutes_invalid(self):
        with pytest.raises(ValueError, match="Format waktu salah"):
            time_to_minutes("25:00")
        with pytest.raises(ValueError, match="Format waktu salah"):
            time_to_minutes("12:60")
        with pytest.raises(ValueError, match="Format waktu salah"):
            time_to_minutes("invalid")

    # Test normalize interval without wrap
    def test_normalize_interval_no_wrap(self):
        start, end = normalize_interval(60, 120)
        assert start == 60
        assert end == 120

    # Test normalize interval with overnight wrap
    def test_normalize_interval_with_wrap(self):
        start, end = normalize_interval(1380, 60)
        assert start == 1380
        assert end == 60 + 1440

    # Test duration calculation same day
    def test_hitung_durasi_same_day(self):
        assert hitung_durasi("09:00", "12:00") == 3
        assert hitung_durasi("14:00", "17:30") == 4
        assert hitung_durasi("10:00", "10:30") == 1

    # Test duration calculation overnight
    def test_hitung_durasi_overnight(self):
        duration = hitung_durasi("23:00", "02:00")
        assert duration == 3

    # Test availability check with no conflicts
    def test_cek_ketersediaan_no_conflicts(self):
        reservations = []
        available, conflicts = cek_ketersediaan_waktu(
            "pvj", "pvj-1", "09:00", "12:00", reservations
        )
        assert available is True
        assert len(conflicts) == 0

    # Test availability check with conflicts
    def test_cek_ketersediaan_with_conflicts(self):
        reservations = [
            {
                "slot_id": "pvj-1",
                "start_time": "10:00",
                "end_time": "14:00",
                "status": "confirmed",
                "id": "test-id-1",
            }
        ]
        available, conflicts = cek_ketersediaan_waktu(
            "pvj", "pvj-1", "09:00", "12:00", reservations
        )
        assert available is False
        assert len(conflicts) == 1
        assert conflicts[0] == "test-id-1"

    # Test availability check different slot
    def test_cek_ketersediaan_different_slot(self):
        reservations = [
            {
                "slot_id": "pvj-2",
                "start_time": "10:00",
                "end_time": "14:00",
                "status": "confirmed",
                "id": "test-id-1",
            }
        ]
        available, conflicts = cek_ketersediaan_waktu(
            "pvj", "pvj-1", "09:00", "12:00", reservations
        )
        assert available is True
        assert len(conflicts) == 0

    # Test availability check with cancelled reservation
    def test_cek_ketersediaan_cancelled_reservation(self):
        reservations = [
            {
                "slot_id": "pvj-1",
                "start_time": "10:00",
                "end_time": "14:00",
                "status": "cancelled",
                "id": "test-id-1",
            }
        ]
        available, conflicts = cek_ketersediaan_waktu(
            "pvj", "pvj-1", "09:00", "12:00", reservations
        )
        assert available is True
        assert len(conflicts) == 0
