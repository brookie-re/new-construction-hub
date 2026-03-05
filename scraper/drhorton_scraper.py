import asyncio
import re
import requests
import uuid
from playwright.async_api import async_playwright
from supabase import create_client

SUPABASE_URL = "https://gytsnlximrlantchvsee.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd5dHNubHhpbXJsYW50Y2h2c2VlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI2NzM5MDEsImV4cCI6MjA4ODI0OTkwMX0.8A1lSPW5K1s_kjWm5gJAjMwUICAsHh5DQCGyBMmSE_E"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd5dHNubHhpbXJsYW50Y2h2c2VlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjY3MzkwMSwiZXhwIjoyMDg4MjQ5OTAxfQ.DG-0zbWJ7bH2N_llHdZinvoVsZCs2VIyd7TI4X4__nE"

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