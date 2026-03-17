# AutoPedicare AI Backend

Backend services and APIs for **AutoPedicare.AI**, handling authentication, data ingestion, AI inference orchestration, and system integrations.

---

## 🚀 Overview

AutoPedicare AI Backend is a robust FastAPI application designed to power the AutoPedicare ecosystem. It features social authentication (Google/Apple), automated audit logging, geolocation tracking, comprehensive fleet management, and a scalable modular architecture.

---

## 🛠️ Technology Stack

- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
- **Database:** PostgreSQL (with [SQLAlchemy](https://www.sqlalchemy.org/) ORM)
- **Migrations:** [Alembic](https://alembic.sqlalchemy.org/)
- **Authentication:** OAuth2 with JWT (Social login via Google & Apple)
- **Validation:** [Pydantic v2](https://docs.pydantic.dev/)
- **Middlewares:** Custom context middleware for device and location tracking

---

## 📂 Project Structure

```text
├── .github/
│   └── workflows/        # GitHub Actions CI/CD pipelines
├── alembic/              # Database migration scripts and configuration
├── app/
│   ├── api/              # API Route definitions
│   │   └── v1/           # Versioned API endpoints
│   │       ├── auth.py   # Authentication endpoints
│   │       └── fleet/    # Fleet Management API endpoints
│   │           ├── vehicles.py
│   │           ├── drivers.py
│   │           ├── assignments.py
│   │           └── trips.py
│   ├── core/             # Core settings, security, and configurations
│   ├── middleware/       # Custom FastAPI middlewares (User Context)
│   ├── models/           # SQLAlchemy DB models
│   │   ├── user.py       # User and authentication models
│   │   ├── audit.py      # Audit logging models
│   │   └── fleet/        # Fleet Management models
│   │       ├── vehicles.py
│   │       ├── drivers.py
│   │       ├── assignments.py
│   │       └── trips.py
│   ├── schemas/          # Pydantic data validation models
│   │   ├── auth.py       # Authentication schemas
│   │   └── fleet/        # Fleet Management schemas
│   │       ├── vehicles.py
│   │       ├── drivers.py
│   │       ├── assignments.py
│   │       └── trips.py
│   ├── services/         # Business logic services
│   │   ├── auth/         # Authentication services
│   │   ├── geo.py        # Geolocation services
│   │   └── fleet/        # Fleet Management services
│   │       ├── vehicles.py
│   │       ├── drivers.py
│   │       ├── assignments.py
│   │       └── trips.py
│   └── main.py           # Application entry point
├── tests/                # Pytest suite for the application
│   ├── auth/             # Authentication tests
│   ├── fleet/            # Fleet Management tests
│   │   ├── test_vehicles.py
│   │   ├── test_drivers.py
│   │   ├── test_assignments.py
│   │   └── test_trips.py
│   └── conftest.py       # Test configuration and fixtures
├── .dockerignore         # Docker exclusion rules
├── .env.sample           # Sample environment variables
├── alembic.ini           # Alembic configuration
├── docker-compose.yml    # Docker services orchestration
├── docker-compose.test.yml # Test database setup
├── Dockerfile            # Backend container definition
└── requirements.txt      # Project dependencies
```

---

## ⚙️ Setup & Installation

### 1. Prerequisites
- Python 3.10+
- PostgreSQL
- Virtual Environment (recommended)

### 2. Environment Configuration
Copy the sample environment file and fill in your credentials:
```bash
cp .env.sample .env
```
Key variables required:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key
- `GOOGLE_CLIENT_ID / APPLE_CLIENT_ID`: Social provider credentials
- `IP_API_KEY`: API key for geolocation services

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Migrations
```bash
alembic upgrade head
```
*Note: This will create tables for users, audit logs, and fleet management (vehicles, drivers, assignments, trips).*

### 5. Run the Application
```bash
uvicorn app.main:app --reload
```
The API will be available at `http://localhost:8000`.

---

## �🐳 Docker Setup

For a containerized environment (recommended for development), you can use Docker Compose. This will spin up both the FastAPI application and a PostgreSQL database.

### 1. Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### 2. Configure Environment
Ensure your `.env` file has the Postgres credentials set:
```bash
POSTGRES_USER=postgres
POSTGRES_PASSWORD=thepassword
POSTGRES_DB=autopedicare
```
*Note: The `DATABASE_URL` is automatically handled inside Docker using the `db` service name.*

### 3. Build and Run
```bash
docker-compose up --build
```

The system will:
1.  Launch a PostgreSQL 16 container.
2.  Wait for the database to be healthy.
3.  Automatically run `alembic upgrade head` to apply migrations.
4.  Start the FastAPI server with hot-reloading enabled.

Access the API at `http://localhost:8000` and the Postgres database at `localhost:5432`.

---

## 🛡️ Core Features

### 👤 Authentication
- **Social Login:** Integrated Google and Apple Identity token verification.
- **JWT Management:** Secure access and refresh token flow.
- **Auto-Provisioning:** Automatic user creation upon first successful social login.

### 📋 Audit & Tracking
- **User Context Middleware:** Automatically extracts IP, device type, OS, and browser from every request.
- **Geolocation:** Integrates with IP-based geolocation services to log the city and country of login attempts.
- **Login History:** Stores detailed audit logs for every authentication event.

### 🧪 Testing
The project uses `pytest` for automated testing with SQLite for fast local testing.

```bash
# Run all tests
pytest

# Run only fleet tests
pytest tests/fleet/

# Run specific test file
pytest tests/fleet/test_vehicles.py

# Run with coverage
pytest --cov=app --cov-report=html
```

**For PostgreSQL testing (CI/CD):**
```bash
# Start test database
docker-compose -f docker-compose.test.yml up -d

# Run tests with PostgreSQL
pytest
```

**Test Coverage Includes:**
- CRUD operations for all entities
- Business rule validation (assignment constraints)
- Duplicate prevention (unique constraints)
- Pagination functionality
- Error handling and status codes
- Data validation and serialization

---

## 📊 Database Design

### Entity Relationship Overview

The database is structured with the following core entities and relationships:

#### **Users Table**
Stores user account information authenticated via social providers.

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| `id` | UUID | PRIMARY KEY | Unique user identifier |
| `email` | String | UNIQUE, NULLABLE | User email address |
| `provider` | String | NOT NULL | Auth provider (google, apple) |
| `provider_id` | String | UNIQUE, NOT NULL | Provider's unique user ID |
| `is_verified` | Boolean | DEFAULT: false | Email verification status |
| `created_at` | DateTime | DEFAULT: NOW | Account creation timestamp |

#### **User Login History Table**
Audits and tracks all user authentication attempts with device and location context.

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| `id` | UUID | PRIMARY KEY | Unique log entry ID |
| `user_id` | UUID | FK → users.id | Associated user |
| `ip_address` | String | - | Login IP address |
| `device` | String | - | Device type (mobile, desktop, tablet) |
| `os` | String | - | Operating system |
| `browser` | String | - | Browser information |
| `latitude` | Float | NULLABLE | Geolocation latitude |
| `longitude` | Float | NULLABLE | Geolocation longitude |
| `country` | String | - | Country from geolocation |
| `city` | String | - | City from geolocation |
| `provider` | String | - | Auth provider used |
| `user_agent` | String | - | Full user agent string |
| `logged_in_at` | DateTime | DEFAULT: NOW | Login timestamp |

#### **Vehicles Table**
Manages fleet vehicle inventory and status.

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| `id` | UUID | PRIMARY KEY | Unique vehicle identifier |
| `plate_number` | String | UNIQUE, NOT NULL | Vehicle registration plate |
| `model` | String | NOT NULL | Vehicle model name |
| `manufacturer` | String | NOT NULL | Vehicle brand/manufacturer |
| `year` | Integer | NOT NULL | Manufacturing year |
| `vehicle_type` | String | NOT NULL | Type (sedan, suv, truck, etc.) |
| `status` | Enum | DEFAULT: active | Status (active, maintenance, inactive) |
| `created_at` | DateTime | DEFAULT: NOW | Creation timestamp |

#### **Drivers Table**
Stores driver profile information and status.

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| `id` | UUID | PRIMARY KEY | Unique driver identifier |
| `full_name` | String | NOT NULL | Driver's full name |
| `license_number` | String | UNIQUE, NOT NULL | Driver's license number |
| `phone_number` | String | NOT NULL | Contact phone number |
| `email` | String | UNIQUE, NOT NULL | Driver's email address |
| `status` | Enum | DEFAULT: active | Status (active, inactive) |
| `created_at` | DateTime | DEFAULT: NOW | Creation timestamp |

#### **Assignments Table**
Links drivers to vehicles, representing vehicle assignments.

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| `id` | UUID | PRIMARY KEY | Unique assignment ID |
| `driver_id` | UUID | FK → drivers.id, NOT NULL | Assigned driver |
| `vehicle_id` | UUID | FK → vehicles.id, NOT NULL | Assigned vehicle |
| `assigned_at` | DateTime | DEFAULT: NOW | Assignment timestamp |
| `status` | Enum | DEFAULT: active | Status (active, inactive) |

#### **Trips Table**
Records individual trips with route, duration, and status information.

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| `id` | UUID | PRIMARY KEY | Unique trip identifier |
| `driver_id` | UUID | FK → drivers.id, NOT NULL | Trip driver |
| `vehicle_id` | UUID | FK → vehicles.id, NOT NULL | Trip vehicle |
| `start_location` | String | NOT NULL | Trip origin address/location |
| `end_location` | String | NOT NULL | Trip destination address/location |
| `start_time` | DateTime | NOT NULL | Trip start timestamp |
| `end_time` | DateTime | NULLABLE | Trip end timestamp |
| `distance_km` | Float | NOT NULL | Total distance traveled |
| `status` | Enum | DEFAULT: ongoing | Status (ongoing, completed, cancelled) |

### Relationships

```
users (1) ──→ (many) user_login_history
drivers (1) ──→ (many) assignments
vehicles (1) ──→ (many) assignments
drivers (1) ──→ (many) trips
vehicles (1) ──→ (many) trips
```

### Key Constraints

- **Unique Constraints:** Plate numbers, license numbers, emails, and provider IDs ensure data integrity
- **Foreign Key Relationships:** All fleet tables reference drivers and vehicles through proper foreign keys
- **Soft Timestamps:** All tables include `created_at` timestamps for audit trails
- **Status Enums:** Vehicle, Driver, Assignment, and Trip statuses are enforced at database level

---

## 🔄 CI/CD Pipelines

The project includes GitHub Actions workflows for continuous integration and testing.

### Continuous Integration (CI)
- **File:** `.github/workflows/ci.yml`
- **Triggers:** 
  - Push events to `main` and `dev` branches
  - Pull requests targeting `main` and `dev` branches
- **Actions:**
  - Python 3.11 environment setup
  - Install dependencies from `requirements.txt`
  - Run full test suite with pytest
  - Generate coverage reports (term-missing format)
  - All tests must pass before merge

**Test Command:**
```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

---
## �📖 API Documentation

The API automatically generates interactive documentation:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---
