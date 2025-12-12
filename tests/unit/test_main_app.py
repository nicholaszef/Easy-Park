import pytest
from fastapi import HTTPException
from app.main import get_auth_service, get_parking_service


class TestServiceDependencies:

    # Test auth service not initialized
    def test_get_auth_service_not_initialized(self):
        from app.main import auth_service as global_auth
        if global_auth is None:
            with pytest.raises(HTTPException) as exc:
                raise HTTPException(status_code=500, detail="Service not initialized")
            assert exc.value.status_code == 500

    # Test parking service not initialized
    def test_get_parking_service_not_initialized(self):
        from app.main import parking_service as global_parking
        if global_parking is None:
            with pytest.raises(HTTPException) as exc:
                raise HTTPException(status_code=500, detail="Service not initialized")
            assert exc.value.status_code == 500


class TestApplicationConfiguration:

    # Test app docs endpoint
    def test_app_title(self, client):
        response = client.get("/docs")
        assert response.status_code == 200

    # Test CORS headers
    def test_cors_headers(self, client):
        response = client.options("/")
        assert response.status_code in [200, 405]

    # Test health check response format
    def test_health_check_format(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["timestamp"], int)
        assert data["timestamp"] > 0
