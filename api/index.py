# Vercel entry point
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.auth_service import AuthService
from app.services.parking_service import ParkingService
import app.main as main_module

# Initialize services for serverless (lifespan doesn't work well)
main_module.auth_service = AuthService()
main_module.parking_service = ParkingService()

# Import app after services are initialized
from app.main import app

# Export for Vercel - must be named 'app' for FastAPI
app = app
