import asyncio
import re
import requests
import uuid
from playwright.async_api import async_playwright
from supabase import create_client

SUPABASE_URL = "https://gytsnlximrlantchvsee.supabase.co"
from config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

COMMUNITY_URLS = [
    {
        "url": "https://www.drhorton.com/alabama/huntsville/huntsville/grand-hollow",
        "name": "Grand Hollow",
        "city": "Huntsville",
        "latitude": 34.7938,
        "longitude": -86.5647
    },
    {
        "url": "https://www.drhorton.com/alabama/huntsville/madison/wheeler-lake-at-greenbrier-preserve",
        "name": "Wheeler Lake at Greenbrier Preserve",
        "city": "Madison",
        "latitude": 34.7721,
        "longitude": -86.7481
    },
    {
        "url": "https://www.drhorton.com/alabama/huntsville/huntsville/highland-hills",
        "name": "Highland Hills",
        "city": "Huntsville",
        "latitude": 34.8012,
        "longitude": -86.6201
    },
    {
        "url": "https://www.drhorton.com/alabama/huntsville/huntsville/wyndhurst-manor-south",
        "name": "Wyndhurst Manor South",
        "city": "Huntsville",
        "latitude": 34.8350,
        "longitude": -86.7200
    },
    {
        "url": "https://www.drhorton.com/alabama/huntsville/huntsville/wyndhurst-manor",
        "name": "Wyndhurst Manor",
        "city": "Huntsville",
        "latitude": 34.8380,
        "longitude": -86.7220
    },
    {
        "url": "https://www.drhorton.com/alabama/huntsville/owens-cross-roads/eagle-trace",
        "name": "Eagle Trace",
        "city": "Owens Cross Roads",
        "latitude": 34.6312,
        "longitude": -86.5401
    },
    {
        "url": "https://www.drhorton.com/alabama/huntsville/owens-cross-roads/sequoyah-cove",
        "name": "Sequoyah Cove",
        "city": "Owens Cross Roads",
        "latitude": 34.6280,
        "longitude": -86.5350
    },
    {
        "url": "https://www.drhorton.com/alabama/huntsville/huntsville/deerfield",
        "name": "Deerfield",
        "city": "Huntsville",
        "latitude": 34.7650,
        "longitude": -86.5100
    },
    {
        "url": "https://www.drhorton.com/alabama/huntsville/meridianville/brier-creek",
        "name": "Brier Creek",
        "city": "Meridianville",
        "latitude": 34.8720,
        "longitude": -86.5680
    },
    {
        "url": "https://www.drhorton.com/alabama/huntsville/gurley/wilson-cove",
        "name": "Wilson Cove",
        "city": "Gurley",
        "latitude": 34.7180,
        "longitude": -86.3720
    },
    {
        "url": "https://www.drhorton.com/alabama/huntsville/gurley/the-willows-at-wilson-cove",
        "name": "The Willows at Wilson Cove",
        "city": "Gurley",
        "latitude": 34.7200,
        "longitude": -86.3700
    },
    {
        "url": "https://www.drhorton.com/alabama/huntsville/madison/southern-landing",
        "name": "Southern Landing",
        "city": "Madison",
        "latitude": 34.7580,
        "longitude": -86.7650
    },
    {
        "url": "https://www.drhorton.com/alabama/huntsville/harvest/oak-forest",
        "name": "Oak Forest",
        "city": "Harvest",
        "latitude": 34.8650,
        "longitude": -86.7450
    },
    {
        "url": "https://www.drhorton.com/alabama/huntsville/harvest/trestle-point",
        "name": "Trestle Point",
        "city": "Harvest",
        "latitude": 34.8700,
        "longitude": -86.7500
    },
    {
        "url": "https://www.drhorton.com/alabama/huntsville/madison/inverness-springs",
        "name": "Inverness Springs",
        "city": "Madison",
        "latitude": 34.7490,
        "longitude": -86.7580
    },
    {
        "url": "https://www.drhorton.com/alabama/huntsville/meridianville/kensington",
        "name": "Kensington",
        "city": "Meridianville",
        "latitude": 34.8800,
        "longitude": -86.5750
    },
    {
        "url": "https://www.drhorton.com/alabama/huntsville/athens/stoney-point",
        "name": "Stoney Point",
        "city": "Athens",
        "latitude": 34.8021,
        "longitude": -86.9710
    },
    {
        "url": "https://www.drhorton.com/alabama/huntsville/madison/sweetwater-at-greenbrier-preserve",
        "name": "Sweetwater at Greenbrier Preserve",
        "city": "Madison",
        "latitude": 34.7700,
        "longitude": -86.7520
    },
    {
        "url": "https://www.drhorton.com/alabama/huntsville/madison/greenbrier-estates-at-greenbrier-preserve",
        "name": "Greenbrier Estates at Greenbrier Preserve",
        "city": "Madison",
        "latitude": 34.7680,
        "longitude": -86.7500
    },
    {
        "url": "https://www.drhorton.com/alabama/huntsville/madison/heritage-park-at-greenbrier-preserve",
        "name": "Heritage Park at Greenbrier Preserve",
        "city": "Madison",
        "latitude": 34.7660,
        "longitude": -86.7510
    },
    {
        "url": "https://www.drhorton.com/alabama/huntsville/madison/greenbrier-preserve",
        "name": "Greenbrier Preserve",
        "city": "Madison",
        "latitude": 34.7640,
        "longitude": -86.7490
    },
    {
        "url": "https://www.drhorton.com/alabama/huntsville/hazel-green/townsend-farms",
        "name": "Townsend Farms",
        "city": "Hazel Green",
        "latitude": 34.9280,
        "longitude": -86.6210
    },
    {
        "url": "https://www.drhorton.com/alabama/huntsville/new-hope/huntland-estates",
        "name": "Huntland Estates",
        "city": "New Hope",
        "latitude": 34.6950,
        "longitude": -86.4020
    },
    {
        "url": "https://www.drhorton.com/alabama/huntsville/athens/abbey-brook",
        "name": "Abbey Brook",
        "city": "Athens",
        "latitude": 34.8050,
        "longitude": -86.9680
    },
    {
        "url": "https://www.drhorton.com/alabama/huntsville/athens/the-links-at-canebrake",
        "name": "The Links at Canebrake",
        "city": "Athens",
        "latitude": 34.8030,
        "longitude": -86.9650
    },
    {
        "url": "https://www.drhorton.com/alabama/huntsville/athens/waters-edge",
        "name": "Waters Edge",
        "city": "Athens",
        "latitude": 34.8010,
        "longitude": -86.9630
    }
]

def upload_image(image_url, address):
    try:
        # Download image from DR Horton
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(image_url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"  ⚠️ Could not download image: {response.status_code}")
            return None

        # Create unique filename from address
        filename = address.lower().replace(' ', '-').replace(',', '') + '.jpg'

        # Upload to Supabase Storage
        supabase_admin.storage.from_('listing-images').upload(
            filename,
            response.content,
            {"content-type": "image/jpeg", "upsert": "true"}
        )

        # Return public URL
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/listing-images/{filename}"
        print(f"  📸 Image uploaded!")
        return public_url

    except Exception as e:
        print(f"  ⚠️ Image upload error: {e}")
        return None

async def scrape_listings(page, community):
    print(f"\nScraping listings for {community['name']}...")

    await page.goto(community['url'], wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_timeout(4000)

    # Get or create community in Supabase
    result = supabase.table('communities').select('id').eq('name', community['name']).execute()
    
    if result.data:
        community_id = result.data[0]['id']
    else:
        insert = supabase.table('communities').insert({
            'name': community['name'],
            'builder': 'D.R. Horton',
            'city': community['city'],
            'state': 'AL',
            'latitude': community['latitude'],
            'longitude': community['longitude'],
        }).execute()
        community_id = insert.data[0]['id']

    print(f"Community ID: {community_id}")

    # Find all listing cards
    cards = await page.query_selector_all('[class*="movein"], [class*="MoveIn"], [class*="home-card"], [class*="HomeCard"], [class*="listing"]')
    print(f"Found {len(cards)} cards")

    for card in cards:
        try:
            card_html = await card.inner_html()
            
            if 'contract' in card_html.lower():
                print("  Skipping under contract listing")
                continue

            # Price
            price_el = await card.query_selector('h2')
            price_text = await price_el.inner_text() if price_el else ""
            price_match = re.search(r'\$([0-9,]+)', price_text)
            price = int(price_match.group(1).replace(',', '')) if price_match else None

            if not price:
                print("  Skipping - no price found")
                continue

            # Address
            address_el = await card.query_selector('h3, h4, .address, [class*="address"]')
            address = await address_el.inner_text() if address_el else "Unknown"
            address = address.strip()

            # Details - beds, baths, garage, stories, sqft
            details_text = await card.inner_text()
            
            beds_match = re.search(r'(\d+)\s*Bed', details_text)
            baths_match = re.search(r'(\d+\.?\d*)\s*Bath', details_text)
            garage_match = re.search(r'(\d+)\s*Garage', details_text)
            stories_match = re.search(r'(\d+)\s*Story', details_text)
            sqft_match = re.search(r'([0-9,]+)\s*Sq\.\s*Ft', details_text)

            beds = int(beds_match.group(1)) if beds_match else None
            baths = float(baths_match.group(1)) if baths_match else None
            garage = int(garage_match.group(1)) if garage_match else None
            stories = int(stories_match.group(1)) if stories_match else None
            sqft = int(sqft_match.group(1).replace(',', '')) if sqft_match else None

            # Image - extract from background-image style
            img_el = await card.query_selector('.card-image')
            image_url = None
            if img_el:
                style = await img_el.get_attribute('style')
                if style:
                    match = re.search(r"url\('([^']+)'\)", style)
                    if match:
                        full_image_url = "https://www.drhorton.com" + match.group(1)
                        # Upload to Supabase Storage
                        image_url = upload_image(full_image_url, address)

            print(f"  ✅ {address} — ${price:,}")

            # Upsert listing
            supabase.table('listings').upsert({
                'community_id': community_id,
                'address': address,
                'price': price,
                'image_url': image_url,
                'beds': beds,
                'baths': baths,
                'garage': garage,
                'stories': stories,
                'sqft': sqft,
                'status': 'available'
            }, on_conflict='address').execute()

        except Exception as e:
            print(f"  ❌ Error on card: {e}")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for community in COMMUNITY_URLS:
            await scrape_listings(page, community)

        await browser.close()
        print("\n✅ Done!")

asyncio.run(main())