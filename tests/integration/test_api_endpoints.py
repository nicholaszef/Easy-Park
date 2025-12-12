import pytest


class TestHealthEndpoint:

    # Test health check
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data


class TestRootEndpoint:

    # Test root endpoint
    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data


class TestLoginEndpoint:

    # Test login success
    def test_login_success(self, client):
        response = client.post(
            "/login", json={"username": "user", "password": "12345"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "user"

    # Test login with wrong password
    def test_login_wrong_password(self, client):
        response = client.post(
            "/login", json={"username": "user", "password": "wrongpass"}
        )
        assert response.status_code == 401

    # Test login with nonexistent user
    def test_login_nonexistent_user(self, client):
        response = client.post(
            "/login", json={"username": "nonexistent", "password": "12345"}
        )
        assert response.status_code == 401

    # Test login with invalid payload
    def test_login_invalid_payload(self, client):
        response = client.post("/login", json={})
        assert response.status_code == 422


class TestMallEndpoints:

    # Test get all malls
    def test_get_all_malls(self, client):
        response = client.get("/malls")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    # Test get mall by id
    def test_get_mall_by_id(self, client):
        response = client.get("/malls/pvj")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "pvj"

    # Test get mall not found
    def test_get_mall_not_found(self, client):
        response = client.get("/malls/nonexistent")
        assert response.status_code == 404

    # Test get slots for mall
    def test_get_slots_for_mall(self, client):
        response = client.get("/malls/pvj/slots")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all(s["mall_id"] == "pvj" for s in data)

    # Test get slot by id
    def test_get_slot_by_id(self, client):
        response = client.get("/malls/pvj/slots/pvj-1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "pvj-1"

    # Test get slot not found
    def test_get_slot_not_found(self, client):
        response = client.get("/malls/pvj/slots/nonexistent")
        assert response.status_code == 404


class TestSlotAvailability:

    # Test check availability success
    def test_check_availability_success(self, client):
        response = client.post(
            "/malls/pvj/slots/pvj-1/check-availability",
            json={"start_time": "09:00", "end_time": "12:00"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "available" in data
        assert "conflicts" in data

    # Test check availability invalid time
    def test_check_availability_invalid_time(self, client):
        response = client.post(
            "/malls/pvj/slots/pvj-1/check-availability",
            json={"start_time": "25:00", "end_time": "12:00"},
        )
        assert response.status_code == 422

    # Test check availability nonexistent mall
    def test_check_availability_nonexistent_mall(self, client):
        response = client.post(
            "/malls/nonexistent/slots/slot-1/check-availability",
            json={"start_time": "09:00", "end_time": "10:00"}
        )
        assert response.status_code == 404

    # Test check availability nonexistent slot
    def test_check_availability_nonexistent_slot(self, client):
        response = client.post(
            "/malls/pvj/slots/nonexistent/check-availability",
            json={"start_time": "09:00", "end_time": "10:00"}
        )
        assert response.status_code == 404

    # Test check availability occupied slot
    def test_check_availability_occupied_slot(self, client):
        response = client.post(
            "/malls/pvj/slots/pvj-3/check-availability",
            json={"start_time": "09:00", "end_time": "10:00"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False
        assert "Slot sedang dipakai" in data["message"]


class TestReservationEndpoints:

    # Test create reservation unauthorized
    def test_create_reservation_unauthorized(self, client, sample_reservation_data):
        response = client.post("/reservations", json=sample_reservation_data)
        assert response.status_code == 401

    # Test create reservation success
    def test_create_reservation_success(
        self, client, auth_headers, sample_reservation_data
    ):
        response = client.post(
            "/reservations", json=sample_reservation_data, headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["mall_id"] == "pvj"
        assert data["status"] == "confirmed"

    # Test get reservations unauthorized
    def test_get_reservations_unauthorized(self, client):
        response = client.get("/reservations")
        assert response.status_code == 401

    # Test get reservations success
    def test_get_reservations_success(self, client, auth_headers):
        response = client.get("/reservations", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestAdminEndpoints:

    # Test admin stats unauthorized
    def test_admin_stats_unauthorized(self, client):
        response = client.get("/admin/stats")
        assert response.status_code == 401

    # Test admin stats forbidden for regular user
    def test_admin_stats_forbidden(self, client, auth_headers):
        response = client.get("/admin/stats", headers=auth_headers)
        assert response.status_code == 403

    # Test admin stats success
    def test_admin_stats_success(self, client, admin_headers):
        response = client.get("/admin/stats", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_reservations" in data
        assert "total_revenue" in data
        assert "active_reservations" in data
        assert "total_malls" in data
        assert "total_slots" in data
        assert isinstance(data["total_reservations"], int)
        assert isinstance(data["total_revenue"], (int, float))


class TestReservationDetails:

    # Test get reservation by id success
    def test_get_reservation_by_id_success(self, client, auth_headers, sample_reservation_data):
        create_response = client.post(
            "/reservations",
            json=sample_reservation_data,
            headers=auth_headers
        )
        assert create_response.status_code == 201
        reservation_id = create_response.json()["id"]

        response = client.get(f"/reservations/{reservation_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == reservation_id

    # Test get reservation nonexistent
    def test_get_reservation_nonexistent(self, client, auth_headers):
        response = client.get("/reservations/nonexistent-id", headers=auth_headers)
        assert response.status_code == 404

    # Test get reservation unauthorized
    def test_get_reservation_unauthorized(self, client):
        response = client.get("/reservations/some-id")
        assert response.status_code == 401
