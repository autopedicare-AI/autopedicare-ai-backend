import httpx
from loguru import logger
from app.core.config import settings

GEO_IP_API_URL = "https://ipinfo.io/"


async def get_location_from_ip(ip: str):
    try:
        timeout = httpx.Timeout(10.0, connect=3.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            url = f"{GEO_IP_API_URL}{ip}/json?token={settings.IP_API_KEY}"
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            # ipinfo returns 'loc' as "lat,lon" string
            loc = data.get("loc", "")
            lat, lon = None, None
            if loc:
                parts = loc.split(",")
                if len(parts) == 2 and parts[0] and parts[1]:
                    try:
                        lat = float(parts[0])
                        lon = float(parts[1])
                    except ValueError as e:
                        logger.warning(
                            "Invalid loc in geolocation response: {loc} | error={error}",
                            loc=loc,
                            error=e,
                        )

            return {
                "country": data.get("country"),
                "state": data.get("region"),
                "city": data.get("city"),
                "latitude": lat,
                "longitude": lon,
            }
    except Exception:
        logger.exception("Error fetching geolocation for IP {ip}", ip=ip)
        return {
            "country": None,
            "state": None,
            "city": None,
            "latitude": None,
            "longitude": None,
        }
