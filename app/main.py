from fastapi import FastAPI, Request
from loguru import logger
from app.middleware.context import UserContextMiddleware
from app.api.v1.auth import router as auth_router


logger.add("app.log", rotation="1 day", retention="7 days", level="INFO")
logger.add(lambda msg: print(msg, end=""), level="INFO", format="{time} - {name} - {level} - {message}")

app = FastAPI(title="AutoPedicare API")

app.add_middleware(UserContextMiddleware)
app.include_router(auth_router, prefix="/api/v1")


@app.get("/")
async def read_root():
    return {"message": "Welcome to the AutoPedicare API!"}


@app.get("/debug-middleware")
async def debug_middleware(request: Request):
    return request.state.context
