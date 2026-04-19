# AutoPedicare AI Backend

Backend services and APIs for **AutoPedicare.AI**, handling authentication, fleet management, E-commerce, AI visual part scanning, and secure payments.

---

## 🚀 Overview

AutoPedicare AI Backend is a production-grade FastAPI application designed to power a modern automotive ecosystem. It bridges the gap between vehicle maintenance and part acquisition through AI-driven visual scanning, intelligent compatibility matching, and a robust multi-vendor e-commerce platform.

---

## 🛠️ Technology Stack

- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
- **Database:** PostgreSQL (with [SQLAlchemy 2.0+](https://www.sqlalchemy.org/) ORM)
- **Migrations:** [Alembic](https://alembic.sqlalchemy.org/)
- **Authentication:** OAuth2 with JWT (Social login via Google & Apple)
- **Cloud Storage:** AWS S3 (for product images and AI scan artifacts)
- **Payments:** Paystack SDK Integration
- **Observability:** [Loguru](https://github.com/Delgan/loguru) (Structured JSON logging for production)
- **Validation:** [Pydantic v2](https://docs.pydantic.dev/)

---

## 📂 Project Structure

```text
├── alembic/              # Database migration scripts
├── app/
│   ├── api/              # API Route definitions
│   │   └── v1/           # Versioned API endpoints
│   │       ├── auth.py   # Authentication
│   │       ├── e_commerce/ # Products, Carts, Orders, Vendors, AI scans
│   │       ├── fleet/    # Fleet Management
│   │       └── payment/  # Secure payment processing
│   ├── core/             # Settings, Security, and Production-grade Logging
│   ├── middleware/       # Custom Middlewares (RequestContext, Logging)
│   ├── models/           # SQLAlchemy DB models for all domains
│   ├── schemas/          # Pydantic data validation models
│   ├── services/         # Domain-driven Business Logic
│   │   ├── e_commerce/   # Compatibility Engine, Multi-vendor Logic
│   │   ├── fleet/        # Vehicle & Trip management
│   │   └── payment/      # Paystack integration services
│   └── main.py           # Application entry point
├── tests/                # Comprehensive Pytest suite
└── requirements.txt      # Project dependencies
```

---

## ⚙️ Setup & Installation

### 1. Prerequisites
- Python 3.10+
- PostgreSQL
- AWS Credentials (for S3)
- Paystack API Credentials

### 2. Environment Configuration
Copy the sample environment file and fill in your credentials:
```bash
cp .env.sample .env
```
Key sections to configure:
- `DATABASE_URL`: PostgreSQL connection string
- `AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY`: Credentials for S3 file storage
- `PAYSTACK_SECRET_KEY`: Secret keys for payment processing
- `GOOGLE_CLIENT_ID / APPLE_CLIENT_ID`: Provider credentials for social login

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Migrations
```bash
alembic upgrade head
```

### 5. Run the Application
```bash
uvicorn app.main:app --reload
```
API Documentation will be available at `http://localhost:8000/docs`.

---

## 🛡️ Core Features

### 🛒 E-Commerce & Inventory
- **Multi-Vendor Support:** Scalable system for independent vendors to manage product listings.
- **Intelligent Cart System:** Handles complex multi-vendor checkouts and real-time inventory checks.
- **Automated Orders:** End-to-end order processing, from placement to payment verification.

### 🧠 Compatibility & AI Visual Scanning
- **Visual Part Scanning:** AI-powered identification of vehicle parts from uploaded images.
- **Matching Engine:** Intelligent logic to match identified parts with vehicle-specific specifications (Year, Brand, Model).
- **Stock Validation:** Immediate feedback on part availability for specific vehicle variants.

### 💳 Secure Payments
- **Paystack Integration:** Seamless payment flow for order fulfillment using Paystack's secure API.
- **Transaction Verification:** Automated webhook and API-based payment status reconciliation.

### 🏢 Fleet Management
- **Vehicle Lifecycle:** Track assignments, status, and maintenance needs.
- **Trip Log:** Automated geolocation tracking and historical trip auditing.

### 👤 Identity & Access
- **Social Connect:** Native integration with Apple and Google Auth.
- **Context Awareness:** Automated tracking of IP, device, and location for every login event via custom middleware.

---

## 📊 Logging & Observability

The backend implements a production-ready observability stack:

- **Request IDs:** Every log entry is tagged with a unique `request_id` for end-to-end tracing across services.
- **Structured Logging:** Production logs are formatted as JSON for easy ingestion into log management systems (ELK, CloudWatch, Datadog).
- **Library Interception:** Automatically intercepts standard library logs (Uvicorn, SQLAlchemy) into the structured flow.
- **Performance Insight:** Automatic duration tracking for all incoming requests to monitor API latency.

---

## 🧪 Testing

The project uses `pytest` for automated testing with support for both SQLite (local) and PostgreSQL (CI/CD).

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html
```

---

## 🔄 CI/CD Pipelines

The project includes GitHub Actions workflows for continuous integration:
- Automated dependency installation.
- Full test suite execution on every pull request.
- Coverage reporting and performance auditing.

---

## 📖 API Documentation

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
