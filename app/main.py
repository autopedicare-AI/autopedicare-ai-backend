from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from app.middleware.context import UserContextMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.api.v1.auth import router as auth_router, get_current_user
from app.api.v1.fleet.assignments import router as assignments_router
from app.api.v1.fleet.drivers import router as drivers_router
from app.api.v1.fleet.trips import router as trips_router
from app.api.v1.fleet.vehicles import router as vehicles_router


logger.add(
    lambda msg: print(msg, end=""),
    level="INFO",
    colorize=True,
    format="{time} - {name} - {level} - {message}",
)

app = FastAPI(title="AutoPedicare API")

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(UserContextMiddleware)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(
    assignments_router, prefix="/api/v1", tags=["Assignments"], dependencies=[Depends(get_current_user)]
)
app.include_router(
    drivers_router, prefix="/api/v1", tags=["Drivers"], dependencies=[Depends(get_current_user)]
)
app.include_router(
    trips_router, prefix="/api/v1", tags=["Trips"], dependencies=[Depends(get_current_user)]
)
app.include_router(
    vehicles_router, prefix="/api/v1", tags=["Vehicles"], dependencies=[Depends(get_current_user)]
)


@app.get("/")
async def read_root():
    return {"message": "Welcome to the AutoPedicare API!"}


@app.get("/debug-middleware")
async def debug_middleware(request: Request):
    return request.state.context
