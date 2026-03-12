import asyncio
import re
import json
import requests
from playwright.async_api import async_playwright
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


COMMUNITIES = [
    {"name": "Bradford Station", "city": "Madison", "lat": 34.7490, "lng": -86.7580, "url": "https://www.lennar.com/new-homes/alabama/huntsville/madison/bradford-station"},
    {"name": "Cedar Springs", "city": "Trinity", "lat": 34.5980, "lng": -87.0830, "url": "https://www.lennar.com/new-homes/alabama/huntsville/trinity/cedar-springs"},
    {"name": "Clift Farm", "city": "Madison", "lat": 34.7450, "lng": -86.7480, "url": "https://www.lennar.com/new-homes/alabama/huntsville/madison/clift-farm"},
    {"name": "Covington Cove", "city": "Athens", "lat": 34.8021, "lng": -86.9710, "url": "https://www.lennar.com/new-homes/alabama/huntsville/athens/covington-cove"},
    {"name": "Craft Springs", "city": "Athens", "lat": 34.8050, "lng": -86.9680, "url": "https://www.lennar.com/new-homes/alabama/huntsville/athens/craft-springs"},
    {"name": "Henderson Estates", "city": "Athens", "lat": 34.8030, "lng": -86.9650, "url": "https://www.lennar.com/new-homes/alabama/huntsville/athens/henderson-estates"},
    {"name": "Highlands Trail", "city": "Harvest", "lat": 34.8650, "lng": -86.7450, "url": "https://www.lennar.com/new-homes/alabama/huntsville/harvest/highlands-trail"},
    {"name": "Hitching Post Farms", "city": "Madison", "lat": 34.7600, "lng": -86.7500, "url": "https://www.lennar.com/new-homes/alabama/huntsville/madison/hitching-post-farms"},
    {"name": "Kendall Trails", "city": "Toney", "lat": 34.8950, "lng": -86.6800, "url": "https://www.lennar.com/new-homes/alabama/huntsville/toney/kendall-trails"},
    {"name": "Lucas Ferry Farms", "city": "Athens", "lat": 34.8010, "lng": -86.9630, "url": "https://www.lennar.com/new-homes/alabama/huntsville/athens/lucas-ferry-farms"},
    {"name": "Natures Walk on the Flint", "city": "Owens Cross Roads", "lat": 34.6280, "lng": -86.5350, "url": "https://www.lennar.com/new-homes/alabama/huntsville/owens-cross-roads/natures-walk-on-the-flint"},
    {"name": "Olde Savannah", "city": "New Market", "lat": 34.9080, "lng": -86.4480, "url": "https://www.lennar.com/new-homes/alabama/huntsville/new-market/olde-savannah"},
    {"name": "Southern Springs", "city": "Harvest", "lat": 34.8700, "lng": -86.7500, "url": "https://www.lennar.com/new-homes/alabama/huntsville/harvest/southern-springs"},
    {"name": "Southern Trail", "city": "Huntsville", "lat": 34.7650, "lng": -86.5100, "url": "https://www.lennar.com/new-homes/alabama/huntsville/huntsville/southern-trail"},
    {"name": "The Reserve at the Retreat", "city": "Meridianville", "lat": 34.8800, "lng": -86.5750, "url": "https://www.lennar.com/new-homes/alabama/huntsville/meridianville/the-reserve-at-the-retreat"},
    {"name": "The Retreat", "city": "Meridianville", "lat": 34.8780, "lng": -86.5730, "url": "https://www.lennar.com/new-homes/alabama/huntsville/meridianville/the-retreat"},
    {"name": "St. Clair Place", "city": "Huntsville", "lat": 34.7850, "lng": -86.6350, "url": "https://www.lennar.com/new-homes/alabama/huntsville/huntsville/st-clair-place"},
    {"name": "Whisper Woods", "city": "Athens", "lat": 34.8010, "lng": -86.9600, "url": "https://www.lennar.com/new-homes/alabama/huntsville/athens/whisper-woods"},
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
            'latitude': community['lat'],
            'longitude': community['lng'],
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
        for community in COMMUNITIES:
            await scrape_listings(page, community)
        await browser.close()
        print("\n✅ Done!")

asyncio.run(main())