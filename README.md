# EasyPark - Parking Reservation System

Production-ready FastAPI microservice untuk sistem reservasi parkir.
---

## Quick Start

### Docker 

```bash
# Start the application
docker compose up app

# Run tests
docker compose up test
```

- **App:** [http://localhost:8000](http://localhost:8000)
- **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

### Local Development

```bash
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000

pytest tests/ -v --cov=app --cov-report=html
```

---

## Features

- **JWT Authentication** - Secure token-based authentication
- **Role-Based Access Control** - Admin and user roles with different permissions
- **Real-time Slot Availability** - Check parking slot availability before booking
- **Conflict Detection** - Automatic detection of overlapping reservations
- **Comprehensive Testing** - 95%+ test coverage with unit, integration, and security tests
- **CI/CD Pipeline** - Automated testing, linting, and Docker builds
- **API Documentation** - Auto-generated Swagger/OpenAPI docs
- **Health Checks** - Built-in health check endpoint for monitoring
- **CORS Support** - Cross-origin resource sharing enabled

---

## Project Structure

```
Easy-Park/
├── app/
│   ├── main.py              
│   ├── models/              
│   │   ├── request.py       
│   │   ├── response.py     
│   │   └── enums.py      
│   ├── services/           
│   │   ├── auth_service.py  
│   │   └── parking_service.py 
│   └── utils/             
│       ├── auth.py         
│       ├── time.py         
│       └── timestamp.py   
├── tests/
│   ├── unit/              
│   ├── integration/        
│   ├── security/          
│   └── conftest.py        
├── data/                  
├── .github/workflows/     
├── Dockerfile              
├── docker-compose.yml       
├── requirements.txt       
├── pyproject.toml         
└── README.md              
```

---

## API Documentation

### Authentication

#### Login
```bash
POST /login
Content-Type: application/json

{
  "username": "user",
  "password": "12345"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "username": "user",
    "role": "user",
    "name": "User"
  }
}
```

**Default Users:**
- Username: `user`, Password: `12345` (User role)
- Username: `admin`, Password: `12345` (Admin role)

### Malls

#### Get All Malls
```bash
GET /malls
```

#### Get Mall by ID
```bash
GET /malls/{mall_id}
```

#### Get Parking Slots for Mall
```bash
GET /malls/{mall_id}/slots
```

#### Check Slot Availability
```bash
POST /malls/{mall_id}/slots/{slot_id}/check-availability
Content-Type: application/json

{
  "start_time": "09:00",
  "end_time": "12:00"
}
```

### Reservations (Requires Authentication)

#### Create Reservation
```bash
POST /reservations
Authorization: Bearer {token}
Content-Type: application/json

{
  "mall_id": "pvj",
  "slot_id": "pvj-1",
  "user_name": "John Doe",
  "vehicle_number": "B1234XYZ",
  "phone": "08123456789",
  "time_slot": {
    "start_time": "09:00",
    "end_time": "12:00"
}
```

#### Get All Reservations
```bash
GET /reservations
Authorization: Bearer {token}
```

#### Get Reservation by ID
```bash
GET /reservations/{reservation_id}
Authorization: Bearer {token}
```

#### Cancel Reservation
```bash
PUT /reservations/{reservation_id}/cancel
Authorization: Bearer {token}
```

### Admin (Admin Role Required)

#### Get Statistics
```bash
GET /admin/stats
Authorization: Bearer {admin_token}
```

**Response:**
```json
{
  "total_reservations": 10,
  "total_revenue": 150000,
  "active_reservations": 5,
  "total_malls": 3,
  "total_slots": 14
}
```

---

## Testing

### Run All Tests

```bash
pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

pytest tests/unit/ -v                    # Unit tests
pytest tests/integration/ -v             # Integration tests
pytest tests/security/ -v                # Security tests
```

### Test Coverage

```bash
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

### Test Structure

```
tests/
├── unit/
│   ├── test_auth_utils.py       # Auth utility tests
│   ├── test_time_utils.py       # Time calculation tests
│   ├── test_auth_service.py     # Auth service tests
│   └── test_parking_service.py  # Parking service tests
├── integration/
│   ├── test_api_endpoints.py         # API endpoint tests
│   └── test_reservation_workflow.py  # Full workflow tests
└── security/
    └── test_security.py         # Security and validation tests
```

---
