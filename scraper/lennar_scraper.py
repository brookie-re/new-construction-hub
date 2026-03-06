import asyncio
import re
import json
import requests
from playwright.async_api import async_playwright
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

COMMUNITY_URLS = [
    {
        "url": "https://www.lennar.com/new-homes/alabama/huntsville/huntsville/st-clair-place",
        "name": "St. Clair Place",
        "city": "Huntsville",
        "latitude": 34.7850,
        "longitude": -86.6350
    }
]

def upload_image(image_url, address):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(image_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        filename = "lennar-" + address.lower().replace(' ', '-').replace(',', '').replace('/', '') + '.jpg'
        supabase_admin.storage.from_('listing-images').upload(
            filename,
            response.content,
            {"content-type": "image/jpeg", "upsert": "true"}
        )
        return f"{SUPABASE_URL}/storage/v1/object/public/listing-images/{filename}"
    except Exception as e:
        print(f"  ⚠️ Image error: {e}")
        return None

async def scrape_listings(page, community):
    print(f"\nScraping {community['name']}...")

    await page.goto(community['url'], wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_timeout(4000)

    # Dismiss cookie popup
    try:
        accept_btn = await page.query_selector('button:has-text("I accept"), button:has-text("Accept")')
        if accept_btn:
            await accept_btn.click()
            await page.wait_for_timeout(1000)
            print("  Dismissed cookie popup")
    except:
        pass

# Debug - print all class names on page
    await page.wait_for_timeout(2000)
    html = await page.content()
    # Find the homesite card classes
    idx = html.find('Stockholm')
    if idx > 0:
        print(html[idx-800:idx+200])

    # Get or create community
    result = supabase.table('communities').select('id').eq('name', community['name']).execute()
    if result.data:
        community_id = result.data[0]['id']
    else:
        insert = supabase.table('communities').insert({
            'name': community['name'],
            'builder': 'Lennar',
            'city': community['city'],
            'state': 'AL',
            'latitude': community['latitude'],
            'longitude': community['longitude'],
        }).execute()
        community_id = insert.data[0]['id']

    print(f"Community ID: {community_id}")

    # Extract JSON-LD structured data
    json_ld = await page.query_selector('script[type="application/ld+json"]')
    if not json_ld:
        print("No JSON-LD found")
        return

    json_text = await json_ld.inner_text()
    data = json.loads(json_text)

    # Find all Offer entries (individual homesites)
    offers = []
    def find_offers(obj):
        if isinstance(obj, dict):
            if obj.get('@type') == 'Offer':
                offers.append(obj)
            for v in obj.values():
                find_offers(v)
        elif isinstance(obj, list):
            for item in obj:
                find_offers(item)

    find_offers(data)
    print(f"Found {len(offers)} offers in JSON-LD")

    for offer in offers:
        try:
            name = offer.get('name', '')
            
            # Skip coming soon - no address yet
            if 'coming soon' in name.lower():
                print(f"  Skipping: {name}")
                continue

            price = offer.get('price')
            if not price or float(price) < 100000:
                continue
            price = int(float(price))

            item = offer.get('itemOffered', {})
            address_obj = item.get('address', {})
            address = address_obj.get('streetAddress', 'Unknown')
            beds = item.get('numberOfBedrooms')
            baths = item.get('numberOfFullBathrooms')
            sqft_obj = item.get('floorSize', {})
            sqft = sqft_obj.get('value')
            image_url_raw = item.get('image')

            image_url = None
            if image_url_raw:
                image_url = upload_image(image_url_raw, address)

            print(f"  ✅ {address} — ${price:,}")

            supabase.table('listings').upsert({
                'community_id': community_id,
                'address': address,
                'price': price,
                'beds': beds,
                'baths': baths,
                'sqft': sqft,
                'image_url': image_url,
                'status': 'available'
            }, on_conflict='address').execute()

        except Exception as e:
            print(f"  ❌ Error: {e}")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        for community in COMMUNITY_URLS:
            await scrape_listings(page, community)
        await browser.close()
        print("\n✅ Done!")

asyncio.run(main())