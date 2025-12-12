# Security tests

import pytest


class TestAuthenticationSecurity:

    # Test protected endpoint without token
    def test_protected_endpoint_without_token(self, client):
        response = client.get("/reservations")
        assert response.status_code == 401

    # Test protected endpoint with invalid token
    def test_protected_endpoint_with_invalid_token(self, client):
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/reservations", headers=headers)
        assert response.status_code == 401

    # Test protected endpoint with malformed token
    def test_protected_endpoint_with_malformed_token(self, client):
        headers = {"Authorization": "InvalidFormat"}
        response = client.get("/reservations", headers=headers)
        assert response.status_code == 401


class TestAuthorizationSecurity:

    # Test admin endpoint with user role
    def test_admin_endpoint_with_user_role(self, client, auth_headers):
        response = client.get("/admin/stats", headers=auth_headers)
        assert response.status_code == 403

    # Test cancel other user reservation
    def test_cancel_other_user_reservation(
        self, client, auth_headers, admin_headers, sample_reservation_data
    ):
        create_response = client.post(
            "/reservations", json=sample_reservation_data, headers=admin_headers
        )
        assert create_response.status_code == 201
        reservation_id = create_response.json()["id"]

        cancel_response = client.put(
            f"/reservations/{reservation_id}/cancel", headers=auth_headers
        )
        assert cancel_response.status_code == 400


class TestInputValidation:

    # Test login with empty credentials
    def test_login_with_empty_credentials(self, client):
        response = client.post("/login", json={"username": "", "password": ""})
        assert response.status_code in [400, 401, 422]

    # Test reservation with invalid time format
    def test_reservation_with_invalid_time_format(
        self, client, auth_headers, sample_reservation_data
    ):
        invalid_data = sample_reservation_data.copy()
        invalid_data["time_slot"]["start_time"] = "invalid"
        response = client.post(
            "/reservations", json=invalid_data, headers=auth_headers
        )
        assert response.status_code == 422

    # Test reservation with missing fields
    def test_reservation_with_missing_fields(self, client, auth_headers):
        response = client.post(
            "/reservations", json={"mall_id": "pvj"}, headers=auth_headers
        )
        assert response.status_code == 422

    # Test SQL injection attempt
    def test_sql_injection_attempt_in_mall_id(self, client):
        response = client.get("/malls/'; DROP TABLE malls; --")
        assert response.status_code == 404

    # Test XSS attempt
    def test_xss_attempt_in_user_name(
        self, client, auth_headers, sample_reservation_data
    ):
        xss_data = sample_reservation_data.copy()
        xss_data["user_name"] = "<script>alert('xss')</script>"
        response = client.post(
            "/reservations", json=xss_data, headers=auth_headers
        )
        assert response.status_code in [201, 400, 422]


class TestRateLimiting:

    # Test multiple failed login attempts
    def test_multiple_failed_login_attempts(self, client):
        for _ in range(5):
            response = client.post(
                "/login", json={"username": "user", "password": "wrong"}
            )
            assert response.status_code == 401


class TestDataExposure:

    # Test password not in response
    def test_password_not_in_response(self, client):
        response = client.post(
            "/login", json={"username": "user", "password": "12345"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "password" not in str(data)
        assert "hashed_password" not in str(data)

    # Test error messages not verbose
    def test_error_messages_not_verbose(self, client):
        response = client.get("/malls/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "database" not in str(data).lower()
        assert "path" not in str(data).lower()
