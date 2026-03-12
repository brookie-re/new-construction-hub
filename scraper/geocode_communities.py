import asyncio
import httpx
import os
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Put your key here or load from env
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "AIzaSyBQAIbQFvvBCWyh2YQEA_muVTf17x5MI-A")


async def geocode(client: httpx.AsyncClient, name: str, city: str) -> tuple:
    query = f"{name}, {city}, AL"
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    r = await client.get(url, params={"address": query, "key": GOOGLE_MAPS_API_KEY}, timeout=10)
    data = r.json()
    if data.get("status") == "OK":
        loc = data["results"][0]["geometry"]["location"]
        return loc["lat"], loc["lng"]
    print(f"  ✗ No result for: {query} (status={data.get('status')})")
    return None, None


async def main():
    communities = supabase.table("communities").select("id, name, city, latitude, longitude").execute().data
    print(f"Total communities: {len(communities)}")

    async with httpx.AsyncClient() as client:
        for c in communities:
            lat, lng = await geocode(client, c["name"], c["city"])
            if lat and lng:
                supabase.table("communities").update({
                    "latitude": lat,
                    "longitude": lng,
                }).eq("id", c["id"]).execute()
                print(f"  ✓ {c['name']} | {c['city']} → {lat}, {lng}")
            await asyncio.sleep(0.1)  # be nice to the API

    print("\nDone!")


asyncio.run(main())
