import httpx
from app.core.config import settings

GEO_IP_API_URL = "https://ipinfo.io/"


async def get_location_from_ip(ip: str):
    try:
        async with httpx.AsyncClient() as client:
            url = f"{GEO_IP_API_URL}{ip}/json?token={settings.IP_API_KEY}"
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            # ipinfo returns 'loc' as "lat,lon" string
            lat_lon = data.get("loc", ",").split(",")
            lat = float(lat_lon[0]) if len(lat_lon) > 0 else None
            lon = float(lat_lon[1]) if len(lat_lon) > 1 else None
            
            return {
                "country": data.get("country"),
                "state": data.get("region"),
                "city": data.get("city"),
                "latitude": lat,
                "longitude": lon,
            }
    except Exception as e:
        print(f"Error fetching geolocation: {e}")
        return {
            "country": None,
            "state": None,
            "city": None,
            "latitude": None,
            "longitude": None,
        }
