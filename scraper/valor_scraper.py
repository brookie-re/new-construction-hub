import asyncio
import re
import httpx
from playwright.async_api import async_playwright
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

COMMUNITIES = [
    {"name": "Anslee Farms – The Estates", "city": "Huntsville", "state": "AL", "lat": 34.7938, "lng": -86.6437, "lotvue": "anslee-farms", "url": "https://www.valorcommunities.com/new-homes-in-huntsville/anslee-farms-the-estates/"},
    {"name": "Ashton Springs",             "city": "Huntsville", "state": "AL", "lat": 34.7650, "lng": -86.5100, "lotvue": "ashton-springs", "url": "https://www.valorcommunities.com/new-homes-in-huntsville/ashton-springs/"},
    {"name": "Autumn Woods",               "city": "Madison",    "state": "AL", "lat": 34.7630, "lng": -86.9830, "lotvue": "autumn-woods", "url": "https://www.valorcommunities.com/new-homes-in-huntsville/autumn-woods/"},
    {"name": "Chapel Cove",                "city": "Harvest",    "state": "AL", "lat": 34.8580, "lng": -86.7430, "lotvue": "chapel-cove", "url": "https://www.valorcommunities.com/new-homes-in-huntsville/chapel-cove/"},
    {"name": "Grand Hollow",               "city": "Huntsville", "state": "AL", "lat": 34.8319, "lng": -86.5306, "lotvue": "grand-hollow", "url": "https://www.valorcommunities.com/new-homes-in-huntsville/grand-hollow/"},
    {"name": "Meridia",                    "city": "Huntsville", "state": "AL", "lat": 34.7550, "lng": -86.5000, "lotvue": "meridia", "url": "https://www.valorcommunities.com/new-homes-in-huntsville/meridia/"},
    {"name": "Merrimack",                  "city": "Huntsville", "state": "AL", "lat": 34.7530, "lng": -86.4980, "lotvue": "merrimack", "url": "https://www.valorcommunities.com/new-homes-in-huntsville/merrimack/"},
    {"name": "Newbury",                    "city": "Huntsville", "state": "AL", "lat": 34.7490, "lng": -86.4940, "lotvue": "newbury", "url": "https://www.valorcommunities.com/new-homes-in-huntsville/newbury/"},
    {"name": "The Cottages at Discovery Point", "city": "Huntsville", "state": "AL", "lat": 34.7470, "lng": -86.4920, "lotvue": "the-cottages-at-discovery-point", "url": "https://www.valorcommunities.com/new-homes-in-huntsville/the-cottages-at-discovery-point/"},
    {"name": "Townside at Autumn Woods",   "city": "Madison",    "state": "AL", "lat": 34.7450, "lng": -86.9900, "lotvue": "townside-at-autumn-woods", "url": "https://www.valorcommunities.com/new-homes-in-huntsville/townside-at-autumn-woods/"},
    {"name": "Valley Ridge",               "city": "Huntsville", "state": "AL", "lat": 34.7430, "lng": -86.4880, "lotvue": "valley-ridge", "url": "https://www.valorcommunities.com/new-homes-in-huntsville/valley-ridge/"},
    {"name": "Windermere",                 "city": "Huntsville", "state": "AL", "lat": 34.7410, "lng": -86.4860, "lotvue": "windermere", "url": "https://www.valorcommunities.com/new-homes-in-huntsville/windermere/"},
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

async def get_or_create_community(community):
    existing = supabase.table("communities").select("id").eq("name", community["name"]).eq("builder", "Valor Communities").execute()
    if existing.data:
        return existing.data[0]["id"]
    result = supabase.table("communities").insert({
        "name": community["name"],
        "builder": "Valor Communities",
        "city": community["city"],
        "state": "AL",
        "latitude": community["lat"],
        "longitude": community["lng"],
        "website_url": community["url"],
    }).execute()
    return result.data[0]["id"]

async def scrape_card(card, page):
    try:
        # Address — match through street suffix + optional direction
        addr_el = await card.query_selector('.address .value')
        addr_raw = (await addr_el.inner_text()).strip() if addr_el else ""
        addr_m = re.match(
            r'(\d+\s+[\w\s]+?(?:ST|RD|DR|LN|WAY|CT|BLVD|AVE|PL|CIR|TRL|PASS|LOOP)(?:\s+(?:NW|NE|SW|SE))?)',
            addr_raw, re.IGNORECASE
        )
        addr_line = addr_m.group(1).strip().title() if addr_m else addr_raw.split(',')[0].strip().title()

        # Image — scroll into view to trigger lazy load
        img_url = None
        img_el = await card.query_selector('.image-wrappper img')
        if img_el:
            await img_el.scroll_into_view_if_needed()
            await page.wait_for_timeout(600)
            src = await img_el.get_attribute('src')
            if not src or src.startswith('data:'):
                src = await img_el.get_attribute('data-src')
            if src and src.startswith('http'):
                safe = re.sub(r'[^a-z0-9]', '-', addr_line.lower())[:60]
                img_url = await download_image(src, f"valor-{safe}.jpg")

        # Plan name from h5: "Lot 84 | Laurel"
        h5_el = await card.query_selector('h5')
        h5_text = (await h5_el.inner_text()).strip() if h5_el else ""
        plan_m = re.search(r'\|\s*(.+)', h5_text)
        plan_name = plan_m.group(1).strip() if plan_m else None

        # Price
        price_el = await card.query_selector('.sales-price .value')
        price_text = (await price_el.inner_text()).strip() if price_el else ""
        price_m = re.search(r'\$([\d,]+)', price_text)
        price = int(price_m.group(1).replace(',', '')) if price_m else None

        # Stats — use img alt text (case-insensitive) to identify each field
        beds = baths = garage = stories = sqft = None
        stat_items = await card.query_selector_all('.inventory_plan_info li')
        for item in stat_items:
            img_el2 = await item.query_selector('img')
            alt = (await img_el2.get_attribute('alt')).strip().lower() if img_el2 else ""
            val_el = await item.query_selector('div:first-child')
            val_text = (await val_el.inner_text()).strip() if val_el else ""
            val_text = val_text.split('/')[0].strip()  # handle "3/4" beds
            try:
                if alt == "bedrooms":
                    beds = int(val_text)
                elif alt == "bathrooms":
                    baths = float(val_text)
                elif alt == "garage":
                    garage = int(val_text)
                elif alt == "floors":
                    stories = int(val_text)
                elif alt == "square feet":
                    sqft = int(val_text)
            except ValueError:
                pass

        return {
            "address": addr_line,
            "plan_name": plan_name,
            "price": price,
            "beds": beds,
            "baths": baths,
            "garage": garage,
            "stories": stories,
            "sqft": sqft,
            "image_url": img_url,
        }

    except Exception as e:
        print(f"  Card parse error: {e}")
        return None

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})

        await page.goto("https://valorcommunities.lotvue.com/regions/HUNTSVILLE", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)

        # Click first community link to trigger full listing load
        link = await page.query_selector("a[href='#comm-anslee-farms']")
        if link:
            await link.click()
            await page.wait_for_timeout(5000)

        # Get count per community from section headers
        counts = []
        for community in COMMUNITIES:
            section = await page.query_selector(f"#comm-{community['lotvue']}")
            if section:
                text = await section.inner_text()
                m = re.search(r'(\d+) Available', text)
                count = int(m.group(1)) if m else 0
            else:
                count = 0
            counts.append(count)
            print(f"  {community['name']}: {count} listings")

        # Get all cards in page order
        all_cards = await page.query_selector_all('.inventory-list-item')
        print(f"\nTotal cards on page: {len(all_cards)}")

        # Slice cards per community by count
        card_index = 0
        for i, community in enumerate(COMMUNITIES):
            count = counts[i]
            print(f"\nScraping: {community['name']} ({count} listings)")

            if count == 0:
                print("  Skipping")
                continue

            community_cards = all_cards[card_index:card_index + count]
            card_index += count

            community_id = await get_or_create_community(community)

            for card in community_cards:
                listing = await scrape_card(card, page)
                if not listing or not listing["address"]:
                    continue
                try:
                    supabase.table("listings").upsert({
                        "community_id": community_id,
                        "address": listing["address"],
                        "price": listing["price"],
                        "beds": listing["beds"],
                        "baths": listing["baths"],
                        "garage": listing["garage"],
                        "stories": listing["stories"],
                        "sqft": listing["sqft"],
                        "image_url": listing["image_url"],
                        "status": "available",
                    }, on_conflict="address").execute()
                    print(f"  ✓ {listing['address']} | ${listing['price']} | {listing['beds']}bd {listing['baths']}ba {listing['sqft']}sqft | img: {'✓' if listing['image_url'] else '✗'}")
                except Exception as e:
                    print(f"  DB error: {e}")

        await browser.close()
        print("\nDone!")

asyncio.run(main())