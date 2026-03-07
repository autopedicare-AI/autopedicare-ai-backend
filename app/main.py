from fastapi import FastAPI, Request
from app.middleware.context import UserContextMiddleware
from app.api.v1.auth import router as auth_router


app = FastAPI(title="AutoPedicare API")

app.add_middleware(UserContextMiddleware)
app.include_router(auth_router, prefix="/api/v1")


@app.get("/")
async def read_root():
    return {"message": "Welcome to the AutoPedicare API!"}


@app.get("/debug-middleware")
async def debug_middleware(request: Request):
    return request.state.context
