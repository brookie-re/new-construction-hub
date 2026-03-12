import asyncio
import re
import httpx
from playwright.async_api import async_playwright
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

COMMUNITIES = [
    {"name": "Anderson Farm", "city": "Athens", "lat": 34.8021, "lng": -86.9710, "url": "https://www.davidsonhomes.com/states/alabama/huntsville-market-area/athens/anderson-farm/"},
    {"name": "The Meadows", "city": "Athens", "lat": 34.8050, "lng": -86.9680, "url": "https://www.davidsonhomes.com/states/alabama/huntsville-market-area/athens/the-meadows/"},
    {"name": "Chapel Hill", "city": "Athens", "lat": 34.8030, "lng": -86.9650, "url": "https://www.davidsonhomes.com/states/alabama/huntsville-market-area/athens/chapel-hill/"},
    {"name": "Ricketts Farm", "city": "Athens", "lat": 34.8010, "lng": -86.9630, "url": "https://www.davidsonhomes.com/states/alabama/huntsville-market-area/athens/ricketts-farm/"},
    {"name": "Creekside", "city": "Harvest", "lat": 34.8650, "lng": -86.7450, "url": "https://www.davidsonhomes.com/states/alabama/huntsville-market-area/harvest/creekside/"},
    {"name": "Durham Farms", "city": "Harvest", "lat": 34.8700, "lng": -86.7500, "url": "https://www.davidsonhomes.com/states/alabama/huntsville-market-area/harvest/durham-farms/"},
    {"name": "Ivy Hills", "city": "Toney", "lat": 34.8950, "lng": -86.6800, "url": "https://www.davidsonhomes.com/states/alabama/huntsville-market-area/toney/ivy-hills/"},
    {"name": "Kendall Farms", "city": "Toney", "lat": 34.8930, "lng": -86.6780, "url": "https://www.davidsonhomes.com/states/alabama/huntsville-market-area/toney/kendall-farms/"},
    {"name": "Kendall Downs", "city": "Toney", "lat": 34.8910, "lng": -86.6760, "url": "https://www.davidsonhomes.com/states/alabama/huntsville-market-area/toney/kendall-downs/"},
    {"name": "Wood Trail", "city": "Toney", "lat": 34.8890, "lng": -86.6740, "url": "https://www.davidsonhomes.com/states/alabama/huntsville-market-area/toney/wood-trail/"},
    {"name": "Forest Glen", "city": "Hazel Green", "lat": 34.9280, "lng": -86.6210, "url": "https://www.davidsonhomes.com/states/alabama/huntsville-market-area/hazel-green/forest-glen/"},
    {"name": "Heritage Lakes", "city": "New Market", "lat": 34.9100, "lng": -86.4500, "url": "https://www.davidsonhomes.com/states/alabama/huntsville-market-area/new-market/heritage-lakes/"},
    {"name": "Lynn Meadows", "city": "Meridianville", "lat": 34.8800, "lng": -86.5750, "url": "https://www.davidsonhomes.com/states/alabama/huntsville-market-area/meridianville/lynn-meadows/"},
    {"name": "Clearview", "city": "Hazel Green", "lat": 34.9260, "lng": -86.6190, "url": "https://www.davidsonhomes.com/states/alabama/huntsville-market-area/hazel-green/clearview/"},
    {"name": "Walkers Hill", "city": "Meridianville", "lat": 34.8780, "lng": -86.5730, "url": "https://www.davidsonhomes.com/states/alabama/huntsville-market-area/meridianville/walkers-hill/"},
    {"name": "Briercreek", "city": "Meridianville", "lat": 34.8760, "lng": -86.5710, "url": "https://www.davidsonhomes.com/states/alabama/huntsville-market-area/meridianville/briercreek/"},
    {"name": "Pikes Ridge", "city": "Meridianville", "lat": 34.8740, "lng": -86.5690, "url": "https://www.davidsonhomes.com/states/alabama/huntsville-market-area/meridianville/pikes-ridge/"},
    {"name": "Creek Grove", "city": "New Market", "lat": 34.9080, "lng": -86.4480, "url": "https://www.davidsonhomes.com/states/alabama/huntsville-market-area/new-market/creek-grove/"},
    {"name": "Flint Meadows", "city": "New Market", "lat": 34.9060, "lng": -86.4460, "url": "https://www.davidsonhomes.com/states/alabama/huntsville-market-area/new-market/flint-meadows/"},
    {"name": "Jaguar Hills", "city": "Huntsville", "lat": 34.7650, "lng": -86.5100, "url": "https://www.davidsonhomes.com/states/alabama/huntsville-market-area/huntsville/jaguar-hills/"},
    {"name": "Spragins Cove", "city": "Huntsville", "lat": 34.7630, "lng": -86.5080, "url": "https://www.davidsonhomes.com/states/alabama/huntsville-market-area/huntsville/spragins-cove/"},
    {"name": "Blue Spring", "city": "Huntsville", "lat": 34.7610, "lng": -86.5060, "url": "https://www.davidsonhomes.com/states/alabama/huntsville-market-area/huntsville/blue-spring/"},
    {"name": "Evergreen Mill", "city": "Madison", "lat": 34.7490, "lng": -86.7580, "url": "https://www.davidsonhomes.com/states/alabama/huntsville-market-area/madison/evergreen-mill/"},
    {"name": "Riverton Preserve", "city": "Huntsville", "lat": 34.7590, "lng": -86.5040, "url": "https://www.davidsonhomes.com/states/alabama/huntsville-market-area/huntsville/riverton-preserve/"},
    {"name": "Berry Cove", "city": "New Market", "lat": 34.9040, "lng": -86.4440, "url": "https://www.davidsonhomes.com/states/alabama/huntsville-market-area/new-market/berry-cove/"},
    {"name": "Ramsay Cove", "city": "Owens Cross Roads", "lat": 34.6280, "lng": -86.5350, "url": "https://www.davidsonhomes.com/states/alabama/huntsville-market-area/owens-cross-roads/ramsay-cove/"},
    {"name": "The Meadows EH", "city": "Owens Cross Roads", "lat": 34.6260, "lng": -86.5330, "url": "https://www.evermorehomes.com/states/alabama/huntsville-market-area/owens-cross-roads/the-meadows-eh/"},
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

    # Check if community exists, insert if not
    existing = supabase.table("communities").select("id").eq("name", community["name"]).eq("builder", "Davidson Homes").execute()
    if existing.data:
        community_id = existing.data[0]["id"]
    else:
        result = supabase.table("communities").insert({
            "name": community["name"],
            "builder": "Davidson Homes",
            "city": community["city"],
            "state": "AL",
            "latitude": community["lat"],
            "longitude": community["lng"],
            "website_url": community["url"],
        }).execute()
        community_id = result.data[0]["id"]
    
    print(f"  Community ID: {community_id}")

    # Load page
    await page.goto(community["url"], wait_until="networkidle")
    await page.wait_for_timeout(3000)

    # Scroll to trigger lazy loading
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(2000)
    await page.evaluate("window.scrollTo(0, 0)")
    await page.wait_for_timeout(1000)

    # Get all slide cards
    cards = await page.query_selector_all('article')
    print(f"  Found {len(cards)} cards")

    listings_added = 0
    for card in cards:
        try:
            # Skip if no address (floor plan only)
            address_el = await card.query_selector('span.text-grey-500')
            if not address_el:
                continue
            address = (await address_el.inner_text()).strip()
            if not address or len(address) < 5:
                continue
            
            print(f"  IMG found: {img_el is not None}")
            if img_el:
                print(f"  IMG src: {await img_el.get_attribute('src')}")

            # Skip if it's not a move-in ready / under construction (no street number)
            if not re.match(r'^\d+', address):
                continue

            # Plan name
            plan_el = await card.query_selector('h4 a')
            plan_name = (await plan_el.inner_text()).strip() if plan_el else ""

            # Price
            price = None
            price_div = await card.query_selector('div[data-ft-payment="true"]')
            if price_div:
                price_text = await price_div.inner_text()
                price_match = re.search(r'\$([\d,]+)', price_text)
                if price_match:
                    price = int(price_match.group(1).replace(',', ''))

            # Beds / baths / sqft from stats row
            beds = baths = sqft = None
            stats_div = await card.query_selector('div[class*="justify-around"]')
            if stats_div:
                stats_text = await stats_div.inner_text()
                beds_m = re.search(r'(\d+)\s*BD', stats_text, re.IGNORECASE)
                baths_m = re.search(r'([\d.]+)\s*BA', stats_text, re.IGNORECASE)
                sqft_m = re.search(r'([\d,]+)\s*SF', stats_text, re.IGNORECASE)
                if beds_m: beds = int(beds_m.group(1))
                if baths_m: baths = float(baths_m.group(1))
                if sqft_m: sqft = int(sqft_m.group(1).replace(',', ''))

           # Image - it's in a sibling div above the article
            img_url = None
            parent = await card.evaluate_handle("el => el.parentElement")
            img_el = await parent.query_selector('img')
        
            if img_el:
                srcset = await img_el.get_attribute('srcset')
                src = await img_el.get_attribute('src')
                first_src = srcset.split(' ')[0] if srcset else src
                if first_src and first_src.startswith('http'):
                    safe_address = re.sub(r'[^a-z0-9]', '-', address.lower())
                    filename = f"davidson-{safe_address}.jpg"
                    img_url = await download_image(first_src, filename)

            # Upsert listing
            supabase.table("listings").upsert({
                "community_id": community_id,
                "address": address,
                "price": price,
                "beds": beds,
                "baths": baths,
                "sqft": sqft,
                "image_url": img_url,
                "status": "available",
            }, on_conflict="address").execute()

            print(f"  ✓ {address} | {plan_name} | ${price} | {beds}bd/{baths}ba | {sqft} sqft")
            listings_added += 1

        except Exception as e:
            print(f"  Card error: {e}")

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