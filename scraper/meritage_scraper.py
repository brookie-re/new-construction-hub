import asyncio
import httpx
import re
from urllib.parse import unquote
from typing import Optional
from playwright.async_api import async_playwright
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
BUILDER = "Meritage Homes"

API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "ocp-apim-subscription-key": "032d255f912045ceb8a1b4cd3b8c5b91",
    "authorization": "Bearer",
    "referer": "https://www.meritagehomes.com/",
}

COMMUNITY_MAP = {
    "a078a00001Sx1lcAAB": {
        "name": "Walkers Hill",
        "city": "Meridianville",
        "lat": 34.88536, "lng": -86.54536,
        "url": "https://www.meritagehomes.com/state/al/huntsville/walkers-hill",
        "page": "https://www.meritagehomes.com/state/al/huntsville/walkers-hill",
    },
    "a07cw000002Au06AAC": {
        "name": "Kendall Farms",
        "city": "Toney",
        "lat": 34.8870908, "lng": -86.6946846,
        "url": "https://www.meritagehomes.com/state/al/huntsville/kendall-farms",
        "page": "https://www.meritagehomes.com/state/al/huntsville/kendall-farms",
    },
    "a078a00001Sx1mhAAB": {
        "name": "Madison Preserve - Reserve Series",
        "city": "Madison",
        "lat": 34.671185, "lng": -86.804258,
        "url": "https://www.meritagehomes.com/state/al/huntsville/madison-preserve-the-reserve-series",
        "page": "https://www.meritagehomes.com/state/al/huntsville/madison-preserve-the-reserve-series",
    },
    "a078a00001Sx1mcAAB": {
        "name": "Madison Preserve - Estate Series",
        "city": "Madison",
        "lat": 34.671185, "lng": -86.804258,
        "url": "https://www.meritagehomes.com/state/al/huntsville/madison-preserve-the-estate-series",
        "page": "https://www.meritagehomes.com/state/al/huntsville/madison-preserve-the-estate-series",
    },
}

VALID_STATUSES = {"Inventory", "Available"}
SKIP_ALTS = {"mobile logo png", "map"}


async def scrape_images() -> dict:
    """Returns address (title case) → image URL mapping."""
    address_to_image = {}
    pages_to_scrape = list(dict.fromkeys(c["page"] for c in COMMUNITY_MAP.values()))

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for url in pages_to_scrape:
            print(f"  Scraping images from: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(6000)
            for _ in range(5):
                await page.evaluate("window.scrollBy(0, 800)")
                await page.wait_for_timeout(600)

            images = await page.evaluate("""() => {
                const results = [];
                document.querySelectorAll('img').forEach(img => {
                    if (img.alt && img.src && img.src.includes('sitecorecontenthub')) {
                        results.push({ alt: img.alt.trim(), src: img.src });
                    }
                });
                return results;
            }""")

            for img in images:
                alt = img['alt'].strip()
                alt_lower = alt.lower()
                if any(skip in alt_lower for skip in SKIP_ALTS):
                    continue
                if alt_lower.startswith('gallery') or alt_lower.startswith('mth_'):
                    continue
                m = re.search(r'url=(https[^&]+)', img['src'])
                if m:
                    real_url = unquote(m.group(1))
                    addr = alt.title()
                    if addr not in address_to_image:
                        address_to_image[addr] = real_url

        await browser.close()

    print(f"  Found {len(address_to_image)} address→image mappings")
    return address_to_image


async def fetch_lots() -> list:
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://www.meritagehomes.com/state/al/huntsville",
            headers=headers, timeout=30
        )
        lot_ids = list(dict.fromkeys(re.findall(r'a0C[a-zA-Z0-9]{15}', r.text)))
        print(f"  Found {len(lot_ids)} lot IDs on market page")

        if not lot_ids:
            return []

        api_url = f"https://apim-int-wus3-prod.azure-api.net/cache/sf/web-lots?externalId=externalId&lotIds={','.join(lot_ids)}"
        r2 = await client.get(api_url, headers=API_HEADERS, timeout=30)
        return r2.json()["Value"]["lots"]


def get_or_create_community(comm_data: dict) -> int:
    name = comm_data["name"]
    existing = supabase.table("communities").select("id").eq("name", name).eq("builder", BUILDER).execute()
    if existing.data:
        return existing.data[0]["id"]
    result = supabase.table("communities").insert({
        "name": name,
        "builder": BUILDER,
        "city": comm_data["city"],
        "state": "AL",
        "latitude": comm_data["lat"],
        "longitude": comm_data["lng"],
        "website_url": comm_data["url"],
    }).execute()
    print(f"  Created community: {name}")
    return result.data[0]["id"]


async def main():
    print("Scraping images...")
    address_to_image = await scrape_images()

    print("\nFetching lots...")
    lots = await fetch_lots()
    print(f"  Total lots: {len(lots)}")

    huntsville_lots = [
        l for l in lots
        if l.get("community_id") in COMMUNITY_MAP
        and l.get("status") in VALID_STATUSES
        and l.get("construction_stage") == "Construction Complete"
        and l.get("lot_data", {}).get("bedrooms")
    ]
    print(f"  Huntsville move-in ready: {len(huntsville_lots)}\n")

    inserted = updated = errors = 0

    for lot in huntsville_lots:
        comm_data = COMMUNITY_MAP[lot["community_id"]]
        community_id = get_or_create_community(comm_data)

        loc = lot.get("location", {})
        ld = lot.get("lot_data", {})

        address = (loc.get("address1") or "").strip().title()
        if not address or address.lower().startswith("tbd") or "dnu" in address.lower():
            continue

        baths_f = float(ld.get("bathrooms_f") or 0)
        baths_h = float(ld.get("bathrooms_h") or 0)
        baths = baths_f + (0.5 * baths_h if baths_h else 0)

        # Match image by address title case
        image_url = address_to_image.get(address)
        # Fallback: try matching the raw uppercase version
        if not image_url:
            raw_addr = (loc.get("address1") or "").strip()
            image_url = address_to_image.get(raw_addr.title())

        listing = {
            "community_id": community_id,
            "address": address,
            "price": int(lot.get("price_spec")) if lot.get("price_spec") else None,
            "beds": int(ld.get("bedrooms")) if ld.get("bedrooms") else None,
            "baths": baths or None,
            "garage": int(ld.get("garages")) if ld.get("garages") else None,
            "sqft": int(ld.get("square_footage")) if ld.get("square_footage") else None,
            "stories": int(ld.get("stories")) if ld.get("stories") else None,
            "image_url": image_url,
            "status": "available",
        }

        price_str = f"${listing['price']:,}" if listing["price"] else "N/A"
        img_found = "✓ img" if image_url else "✗ no img"

        try:
            supabase.table("listings").insert(listing).execute()
            inserted += 1
            print(f"  ✓ {address} | {comm_data['name']} | {price_str} | {listing['beds']}bd/{listing['baths']}ba | {img_found}")
        except Exception as e:
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                supabase.table("listings").update({
                    k: v for k, v in listing.items() if k != "community_id"
                }).eq("address", address).execute()
                updated += 1
                print(f"  ~ updated {address} | {img_found}")
            else:
                print(f"  ✗ {address}: {e}")
                errors += 1

    print(f"\nDone! Inserted: {inserted} | Updated: {updated} | Errors: {errors}")


asyncio.run(main())