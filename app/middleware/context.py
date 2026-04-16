import uuid
import time
from loguru import logger
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from user_agents import parse
from datetime import datetime, timezone
from app.services.geo import get_location_from_ip
from app.core.logging import request_id_ctx


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
        request_id_ctx.set(request_id)

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
            "Request: {method} {url} | IP: {ip} | Device: {device} | OS: {os} | Browser: {browser}",
            method=request.method,
            url=str(request.url),
            ip=ip,
            device=device,
            os=os,
            browser=browser,
        )

        start_time = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "Unhandled exception | {method} {url} | Duration: {duration:.2f}ms",
                method=request.method,
                url=str(request.url),
                duration=duration_ms,
            )
            raise
        finally:
            pass

        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "Response: {method} {url} | Status: {status} | Duration: {duration:.2f}ms",
            method=request.method,
            url=str(request.url),
            status=response.status_code,
            duration=duration_ms,
        )

        return response
