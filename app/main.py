from fastapi import FastAPI, Request
from app.middleware.context import UserContextMiddleware
from app.api.v1.auth import router as auth_router
from app.api.v1.fleet.vehicles import router as vehicles_router
from app.api.v1.fleet.drivers import router as drivers_router
from app.api.v1.fleet.assignments import router as assignments_router
from app.api.v1.fleet.trips import router as trips_router


app = FastAPI(title="AutoPedicare API")

app.add_middleware(UserContextMiddleware)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(vehicles_router, prefix="/api/v1")
app.include_router(drivers_router, prefix="/api/v1")
app.include_router(assignments_router, prefix="/api/v1")
app.include_router(trips_router, prefix="/api/v1")


@app.get("/")
async def read_root():
    return {"message": "Welcome to the AutoPedicare API!"}


@app.get("/debug-context")
async def debug_context(request: Request):
    return {"captured_data": request.state.context}
