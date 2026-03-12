import asyncio
import httpx
import re
from playwright.async_api import async_playwright
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
BUILDER = "Century Communities"

COMMUNITIES = [
    {
        "name": "Kendall Glades",
        "city": "Toney",
        "state": "AL",
        "lat": 34.8870908, "lng": -86.6946846,
        "url": "https://www.centurycommunities.com/find-your-new-home/alabama/huntsville-metro/toney/kendall-glades/",
        "website_url": "https://www.centurycommunities.com/find-your-new-home/alabama/huntsville-metro/toney/kendall-glades/",
    },
    {
        "name": "Laurenwood",
        "city": "Athens",
        "state": "AL",
        "lat": 34.7698, "lng": -86.9747,
        "url": "https://www.centurycommunities.com/find-your-new-home/alabama/huntsville-metro/athens/laurenwood/",
        "website_url": "https://www.centurycommunities.com/find-your-new-home/alabama/huntsville-metro/athens/laurenwood/",
    },
    {
        "name": "Bermuda Lakes",
        "city": "Meridianville",
        "state": "AL",
        "lat": 34.8577, "lng": -86.5737,
        "url": "https://www.centurycommunities.com/find-your-new-home/alabama/huntsville-metro/meridianville/bermuda-lakes/",
        "website_url": "https://www.centurycommunities.com/find-your-new-home/alabama/huntsville-metro/meridianville/bermuda-lakes/",
    },
]


def get_or_create_community(comm: dict) -> int:
    existing = supabase.table("communities").select("id").eq("name", comm["name"]).eq("builder", BUILDER).execute()
    if existing.data:
        return existing.data[0]["id"]
    result = supabase.table("communities").insert({
        "name": comm["name"],
        "builder": BUILDER,
        "city": comm["city"],
        "state": comm["state"],
        "latitude": comm["lat"],
        "longitude": comm["lng"],
        "website_url": comm["website_url"],
    }).execute()
    print(f"  Created community: {comm['name']}")
    return result.data[0]["id"]


async def fetch_image(img_id: str) -> str:
    url = f"https://www.centurycommunities.com/commerceblocksapi/getimageurls/?ids={img_id}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=15)
        data = r.json()
        imgs = data.get("data", {}).get(img_id, [])
        return imgs[0]["url"] if imgs else None


async def scrape_community(page, comm: dict) -> list:
    print(f"  Scraping: {comm['name']}")
    await page.goto(comm["url"], wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_timeout(6000)
    for _ in range(5):
        await page.evaluate("window.scrollBy(0, 800)")
        await page.wait_for_timeout(600)

    cards = await page.evaluate("""() => {
        const results = [];
        document.querySelectorAll('li[data-price]').forEach(li => {
            results.push({
                price: li.dataset.price,
                sqft: li.dataset.sqft,
                address: (li.querySelector('.street-number-text') || {}).innerText || '',
                beds: (li.querySelector('img[alt="Bedrooms"]')?.parentElement || {}).innerText || '',
                baths: (li.querySelector('img[alt="Bathrooms"]')?.parentElement || {}).innerText || '',
                fullText: li.innerText || '',
                imgId: (li.querySelector('[id^="quick-move-in-gallery-"]') || {}).id || '',
            });
        });
        return results;
    }""")

    return cards


async def main():
    inserted = updated = errors = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})

        for comm in COMMUNITIES:
            community_id = get_or_create_community(comm)
            cards = await scrape_community(page, comm)
            print(f"  Found {len(cards)} listings")

            for card in cards:
                # Clean address - strip lot number
                address = re.sub(r'\s*\|\s*Lot\s*\d+', '', card["address"]).strip().title()
                if not address:
                    continue

                # Parse beds/baths
                beds_match = re.search(r'(\d+)', card["beds"])
                baths_match = re.search(r'(\d+(?:\.\d+)?)', card["baths"])
                garage_match = re.search(r'(\d+)\s*bay', card["fullText"])

                beds = int(beds_match.group(1)) if beds_match else None
                baths = float(baths_match.group(1)) if baths_match else None
                garage = int(garage_match.group(1)) if garage_match else None
                price = int(card["price"]) if card["price"] else None
                sqft = int(card["sqft"]) if card["sqft"] else None

                # Fetch image
                img_id = re.search(r'quick-move-in-gallery-(\d+)', card["imgId"])
                image_url = None
                if img_id:
                    image_url = await fetch_image(img_id.group(1))

                listing = {
                    "community_id": community_id,
                    "address": address,
                    "price": price,
                    "beds": beds,
                    "baths": baths,
                    "garage": garage,
                    "sqft": sqft,
                    "image_url": image_url,
                    "status": "available",
                }

                price_str = f"${price:,}" if price else "N/A"
                img_found = "✓ img" if image_url else "✗ no img"

                try:
                    supabase.table("listings").insert(listing).execute()
                    inserted += 1
                    print(f"  ✓ {address} | {price_str} | {beds}bd/{baths}ba | {img_found}")
                except Exception as e:
                    if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                        supabase.table("listings").update({
                            k: v for k, v in listing.items() if k != "community_id"
                        }).eq("address", address).execute()
                        updated += 1
                        print(f"  ~ updated {address}")
                    else:
                        print(f"  ✗ {address}: {e}")
                        errors += 1

        await browser.close()

    print(f"\nDone! Inserted: {inserted} | Updated: {updated} | Errors: {errors}")


asyncio.run(main())