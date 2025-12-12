# Vercel entry point
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app, auth_service, parking_service
from app.services.auth_service import AuthService
from app.services.parking_service import ParkingService
import app.main as main_module

# Initialize services for serverless (lifespan doesn't work well)
if main_module.auth_service is None:
    main_module.auth_service = AuthService()
if main_module.parking_service is None:
    main_module.parking_service = ParkingService()

# Export for Vercel
handler = app
