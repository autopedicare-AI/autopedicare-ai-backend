from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from app.middleware.context import UserContextMiddleware
from app.api.v1.auth import router as auth_router


logger.add("app.log", rotation="1 day", retention="7 days", level="INFO")
logger.add(lambda msg: print(msg, end=""), level="INFO", format="{time} - {name} - {level} - {message}")

app = FastAPI(title="AutoPedicare API")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(UserContextMiddleware)
app.include_router(auth_router, prefix="/api/v1")


@app.get("/")
async def read_root():
    return {"message": "Welcome to the AutoPedicare API!"}


@app.get("/debug-middleware")
async def debug_middleware(request: Request):
    return request.state.context
