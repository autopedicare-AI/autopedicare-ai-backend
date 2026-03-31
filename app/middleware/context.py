import uuid
from loguru import logger
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from user_agents import parse
from datetime import datetime, timezone
from app.services.geo import get_location_from_ip


class UserContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract Public IP
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        ip = x_forwarded_for.split(",")[0].strip() if x_forwarded_for else request.client.host  # type: ignore

        # Parse User-Agent
        ua_string = request.headers.get("User-Agent", "")
        user_agent = parse(ua_string)

        device = (
            "mobile"
            if user_agent.is_mobile
            else "tablet" if user_agent.is_tablet else "desktop"
        )
        os = user_agent.os.family
        browser = f"{user_agent.browser.family} {user_agent.browser.version_string}"

        location = await get_location_from_ip(ip)

        request_id = str(uuid.uuid4())

        request.state.context = {
            "request_id": request_id,
            "ip": ip,
            "device": device,
            "os": os,
            "browser": browser,
            "user_agent": ua_string,
            "location": location,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(
            f"Request: {request.method} {request.url} | Request ID: {request_id} | IP: {ip} | Device: {device} | OS: {os} | Browser: {browser}"
        )

        try:
            response = await call_next(request)
        except Exception as e:
            logger.exception(
                "Unhandled exception executing request {method} {url} | Request ID: {request_id}",
                method=request.method,
                url=request.url,
                request_id=request_id,
            )
            raise

        logger.info(
            f"Response: {request.method} {request.url} | Request ID: {request_id} | Status: {response.status_code}"
        )

        return response
