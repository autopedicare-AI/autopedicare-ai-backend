from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.middleware.context import UserContextMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.api.dependencies import get_current_user
from app.core.logging import setup_logging

from app.api.v1.auth import router as auth_router
from app.api.v1.fleet.assignments import router as assignments_router
from app.api.v1.fleet.drivers import router as drivers_router
from app.api.v1.fleet.trips import router as trips_router
from app.api.v1.fleet.vehicles import router as vehicles_router

from app.api.v1.e_commerce.carts import router as carts_router
from app.api.v1.e_commerce.compatibilities import router as compatibilities_router
from app.api.v1.e_commerce.orders import router as orders_router
from app.api.v1.e_commerce.products import router as products_router
from app.api.v1.e_commerce.product_images import router as product_images_router
from app.api.v1.e_commerce.scan_parts import router as scan_parts_router
from app.api.v1.e_commerce.vendors import router as vendor_router
from app.api.v1.payment.payment import router as payment_router

# Initialize synchronized production-level logging
setup_logging()

app = FastAPI(title="AutoPedicare API")

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


# Production CORS configuration
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://autopedicare.com",  # Example production domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(UserContextMiddleware)

app.include_router(auth_router, prefix="/api/v1")

fleet_dependencies = [Depends(get_current_user)]
app.include_router(
    assignments_router,
    prefix="/api/v1",
    dependencies=fleet_dependencies,
)
app.include_router(
    drivers_router,
    prefix="/api/v1",
    dependencies=fleet_dependencies,
)
app.include_router(
    trips_router,
    prefix="/api/v1",
    dependencies=fleet_dependencies,
)
app.include_router(
    vehicles_router,
    prefix="/api/v1",
    dependencies=fleet_dependencies,
)

app.include_router(products_router, prefix="/api/v1")
app.include_router(product_images_router, prefix="/api/v1")
app.include_router(vendor_router, prefix="/api/v1")
app.include_router(compatibilities_router, prefix="/api/v1")
app.include_router(scan_parts_router, prefix="/api/v1")


app.include_router(
    carts_router,
    prefix="/api/v1",
    dependencies=[Depends(get_current_user)],
)
app.include_router(
    orders_router,
    prefix="/api/v1",
    dependencies=[Depends(get_current_user)],
)

app.include_router(payment_router, prefix="/api/v1", tags=["Payments"])


@app.get("/health/live")
async def health_live():
    return {"status": "alive"}


@app.get("/health/ready")
async def health_ready():
    return {"status": "ready"}


@app.get("/")
async def read_root():
    return {"message": "Welcome to the AutoPedicare API!"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
