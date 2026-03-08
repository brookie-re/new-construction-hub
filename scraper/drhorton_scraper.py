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