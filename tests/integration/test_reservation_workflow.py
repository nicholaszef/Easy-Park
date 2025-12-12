import pytest


class TestReservationWorkflow:

    # Test complete reservation lifecycle
    def test_complete_reservation_lifecycle(
        self, client, auth_headers, sample_reservation_data
    ):
        # Create reservation
        create_response = client.post(
            "/reservations", json=sample_reservation_data, headers=auth_headers
        )
        assert create_response.status_code == 201
        reservation = create_response.json()
        reservation_id = reservation["id"]

        # Get reservation
        get_response = client.get(
            f"/reservations/{reservation_id}", headers=auth_headers
        )
        assert get_response.status_code == 200
        assert get_response.json()["id"] == reservation_id

        # Cancel reservation
        cancel_response = client.put(
            f"/reservations/{reservation_id}/cancel", headers=auth_headers
        )
        assert cancel_response.status_code == 200

        # Verify cancellation
        verify_response = client.get(
            f"/reservations/{reservation_id}", headers=auth_headers
        )
        assert verify_response.json()["status"] == "cancelled"

    # Test reservation conflict detection
    def test_reservation_conflict_detection(
        self, client, auth_headers, sample_reservation_data
    ):
        # Create first reservation
        create_response1 = client.post(
            "/reservations", json=sample_reservation_data, headers=auth_headers
        )
        assert create_response1.status_code == 201

        # Try to create conflicting reservation
        create_response2 = client.post(
            "/reservations", json=sample_reservation_data, headers=auth_headers
        )
        assert create_response2.status_code == 400

    # Test reservation with invalid mall
    def test_reservation_with_invalid_mall(
        self, client, auth_headers, sample_reservation_data
    ):
        invalid_data = sample_reservation_data.copy()
        invalid_data["mall_id"] = "nonexistent"
        response = client.post(
            "/reservations", json=invalid_data, headers=auth_headers
        )
        assert response.status_code == 400

    # Test reservation with invalid slot
    def test_reservation_with_invalid_slot(
        self, client, auth_headers, sample_reservation_data
    ):
        invalid_data = sample_reservation_data.copy()
        invalid_data["slot_id"] = "nonexistent"
        response = client.post(
            "/reservations", json=invalid_data, headers=auth_headers
        )
        assert response.status_code == 400

    # Test cancel nonexistent reservation
    def test_cancel_nonexistent_reservation(self, client, auth_headers):
        response = client.put(
            "/reservations/nonexistent/cancel", headers=auth_headers
        )
        assert response.status_code == 400
