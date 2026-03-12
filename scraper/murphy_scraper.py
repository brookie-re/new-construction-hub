import asyncio
import re
import json
import httpx
from playwright.async_api import async_playwright
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

COMMUNITIES = [
    {"name": "Ayers Farm", "city": "New Market", "lat": 34.7490, "lng": -86.7580, "url": "https://www.murphyhomesal.com/communities/madison/ayers-farm"},
    {"name": "Chapel Grove", "city": "Athens", "lat": 34.8030, "lng": -86.9650, "url": "https://www.murphyhomesal.com/communities/athens/chapel-grove"},
    {"name": "Greenbrier Hills of Madison", "city": "Madison", "lat": 34.7600, "lng": -86.7500, "url": "https://www.murphyhomesal.com/communities/madison/greenbrier-hills-of-madison"},
    {"name": "Monrovia Springs", "city": "Harvest", "lat": 34.8278, "lng": -86.7110, "url": "https://www.murphyhomesal.com/communities/harvest/monrovia-springs"},
    {"name": "Southern Gayles", "city": "Athens", "lat": 34.7450, "lng": -86.7480, "url": "https://www.murphyhomesal.com/communities/madison/southern-gayles"},
    {"name": "Southern Gayles West", "city": "Athens", "lat": 34.7430, "lng": -86.7460, "url": "https://www.murphyhomesal.com/communities/undefined/southern-gayles-west"},
    {"name": "Star Estates", "city": "Madison", "lat": 34.7410, "lng": -86.7440, "url": "https://www.murphyhomesal.com/communities/undefined/star-estates"},
    {"name": "The Estates at Brierfield", "city": "Meridianville", "lat": 34.8800, "lng": -86.5750, "url": "https://www.murphyhomesal.com/communities/meridianville/the-estates-at-brierfield"},
]

async def download_image(url: str, filename: str):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                supabase_admin.storage.from_("listing-images").upload(
                    filename, r.content, {"content-type": "image/jpeg", "upsert": "true"}
                )
                return f"https://gytsnlximrlantchvsee.supabase.co/storage/v1/object/public/listing-images/{filename}"
    except Exception as e:
        print(f"  Image error: {e}")
    return None

async def scrape_community(page, community: dict):
    print(f"\nScraping: {community['name']} ({community['city']})")

    existing = supabase.table("communities").select("id").eq("name", community["name"]).eq("builder", "Murphy Homes").execute()
    if existing.data:
        community_id = existing.data[0]["id"]
    else:
        result = supabase.table("communities").insert({
            "name": community["name"],
            "builder": "Murphy Homes",
            "city": community["city"],
            "state": "AL",
            "latitude": community["lat"],
            "longitude": community["lng"],
            "website_url": community["url"],
        }).execute()
        community_id = result.data[0]["id"]

    print(f"  Community ID: {community_id}")

    await page.goto(community["url"], wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_timeout(6000)

    state = None
    scripts = await page.query_selector_all('script:not([src])')
    for script in scripts:
        text = await script.inner_text()
        if '__PRELOADED_STATE__' in text:
            match = re.search(r'window\.__PRELOADED_STATE__\s*=\s*({.*})', text, re.DOTALL)
            if match:
                try:
                    state = json.loads(match.group(1))
                except Exception as e:
                    print(f"  JSON parse error: {e}")
            break

    if not state:
        print("  No state found")
        return

    homes_data = state.get('cloudData', {}).get('homes', {})
    homes_list = []
    if isinstance(homes_data, dict):
        for val in homes_data.values():
            if isinstance(val, dict) and 'data' in val and isinstance(val['data'], list):
                homes_list = val['data']
                break
    elif isinstance(homes_data, list):
        homes_list = homes_data

    # Filter to this community only
    cloud_communities = state.get('cloudData', {}).get('communities', {})
    community_cloud_id = None
    if isinstance(cloud_communities, dict):
        for val in cloud_communities.values():
            data = val.get('data', []) if isinstance(val, dict) else []
            for c in data:
                if isinstance(c, dict):
                    name = str(c.get('name', '')).lower()
                    if community['name'].lower() in name or name in community['name'].lower():
                        community_cloud_id = c.get('_id')
                        print(f"  Matched community: {c.get('name')} -> {community_cloud_id}")
                        break

    if community_cloud_id:
        homes_list = [h for h in homes_list if h.get('containedIn') == community_cloud_id]
        print(f"  Filtered to {len(homes_list)} homes for this community")
    else:
        print("  WARNING: Could not match community, using all homes")

    print(f"  Processing {len(homes_list)} homes")
    listings_added = 0

    for home in homes_list:
        try:
            if home.get('status') not in ['Active', 'Under Construction']:
                continue

            street = home.get('address', {}).get('streetAddress', '')
            if not street or not re.match(r'^\d+', street):
                continue

            price = home.get('price')
            beds = home.get('beds')
            baths_full = home.get('bathsFull') or 0
            baths_half = home.get('bathsHalf') or 0
            baths = float(baths_full) + (0.5 if baths_half else 0)
            sqft = home.get('sqft') or home.get('size')

            img_url = None
            photos = home.get('photos') or home.get('elevationPhotos') or []
            if photos:
                raw_url = photos[0].get('contentUrl') if isinstance(photos[0], dict) else str(photos[0])
                if raw_url:
                    safe_address = re.sub(r'[^a-z0-9]', '-', street.lower())
                    filename = f"murphy-{safe_address}.jpg"
                    img_url = await download_image(raw_url, filename)

            supabase.table("listings").upsert({
                "community_id": community_id,
                "address": street,
                "price": int(price) if price else None,
                "beds": int(beds) if beds else None,
                "baths": baths if baths else None,
                "sqft": int(sqft) if sqft else None,
                "image_url": img_url,
                "status": "available",
            }, on_conflict="address").execute()

            print(f"  ✓ {street} | ${price} | {beds}bd/{baths}ba | {sqft} sqft")
            listings_added += 1

        except Exception as e:
            print(f"  Home error: {e}")

    print(f"  Total listings added: {listings_added}")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})

        for community in COMMUNITIES:
            try:
                await scrape_community(page, community)
            except Exception as e:
                print(f"  FAILED {community['name']}: {e}")

        await browser.close()
        print("\nDone!")

asyncio.run(main())