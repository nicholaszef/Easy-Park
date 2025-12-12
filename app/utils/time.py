"""Time calculation utilities."""

import math
from datetime import datetime
from typing import List, Tuple

from ..models.enums import StatusReservasi


def time_to_minutes(t: str) -> int:
    """Convert 'HH:MM' string to minutes (0-1439)."""
    try:
        dt = datetime.strptime(t, "%H:%M")
    except ValueError:
        raise ValueError(f"Format waktu salah: '{t}'. Harus 'HH:MM'.")
    return dt.hour * 60 + dt.minute


def normalize_interval(start_min: int, end_min: int) -> Tuple[int, int]:
    """Normalize time interval, handling midnight wrap."""
    if end_min <= start_min:
        end_min += 24 * 60
    return start_min, end_min


def hitung_durasi(start_time: str, end_time: str) -> int:
    """Calculate duration in hours (rounded up), minimum 1 hour."""
    s_min = time_to_minutes(start_time)
    e_min = time_to_minutes(end_time)
    s_min, e_min = normalize_interval(s_min, e_min)
    total_minutes = e_min - s_min
    hours = math.ceil(total_minutes / 60)
    return max(1, hours)


def cek_ketersediaan_waktu(
    mall_id: str,
    slot_id: str,
    start_time: str,
    end_time: str,
    reservations_db: List[dict],
) -> Tuple[bool, List[str]]:
    """Check time slot availability for a parking slot."""
    conflicts = []
    new_s = time_to_minutes(start_time)
    new_e = time_to_minutes(end_time)
    new_s, new_e = normalize_interval(new_s, new_e)

    for reservasi in reservations_db:
        if reservasi["slot_id"] != slot_id:
            continue
        if reservasi["status"] not in [
            StatusReservasi.CONFIRMED.value,
            StatusReservasi.ACTIVE.value,
        ]:
            continue

        existing_s = time_to_minutes(reservasi["start_time"])
        existing_e = time_to_minutes(reservasi["end_time"])
        existing_s, existing_e = normalize_interval(existing_s, existing_e)

        # Check overlap
        if not (new_e <= existing_s or new_s >= existing_e):
            conflicts.append(reservasi["id"])

    return (len(conflicts) == 0, conflicts)
