import asyncio
import httpx
import json
from typing import Optional
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
BUILDER = "DSLD Homes"
BUILDER_ID = "5702af75f410954eb27ce27a"

HUNTSVILLE_SLUGS = {
    'athens-preserve', 'cedar-gap-estates', 'crystal-creek', 'green-cove',
    'hickory-cove-at-mountain-preserve', 'high-park-at-mountain-preserve',
    'kennesaw-creek', 'malvern-hill', 'mccollum-manor', 'meadow-crest',
    'newby-chapel', 'parkside', 'parvin-place', 'sonoma-valley',
    'the-estates-at-heritage-lakes', 'tunlaw-ridge', 'wingate',
    'browns-crossing', 'carrington-place', 'hawks-landing', 'natures-cove',
    'natures-trail-madison', 'park-place', 'phillips-cove',
    'phillips-cove-cottages', 'plantation-park', 'sweet-stone-farms',
    'the-estates-at-rivers-landing', 'watercress-lakes', 'watercress-springs'
}

# Only scrape homes with these statuses
VALID_STATUSES = {"Active", "Under Construction"}


def get_or_create_community(name: str, lng: Optional[float], lat: Optional[float], slug: str) -> int:
    existing = supabase.table("communities").select("id").eq("name", name).eq("builder", BUILDER).execute()
    if existing.data:
        return existing.data[0]["id"]

    result = supabase.table("communities").insert({
        "name": name,
        "builder": BUILDER,
        "city": "",  # will be inferred from listings
        "state": "AL",
        "latitude": lat,
        "longitude": lng,
        "website_url": f"https://www.dsldhomes.com/communities/alabama/huntsville/{slug}",
    }).execute()
    print(f"  Created community: {name}")
    return result.data[0]["id"]


async def fetch_data() -> tuple:
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://www.dsldhomes.com/communities/alabama/huntsville/kennesaw-creek",
            headers=headers, timeout=30
        )
        html = r.text

    idx = html.find('window.__PRELOADED_STATE__ = ')
    start = idx + len('window.__PRELOADED_STATE__ = ')
    end = html.find('</script>', start)
    data = json.loads(html[start:end].strip().rstrip(';'))

    cloud = data['cloudData']
    homes = cloud['homes'][BUILDER_ID]['data']
    communities = cloud['communities'][BUILDER_ID]['data']
    return homes, communities


async def main():
    print("Fetching DSLD data...")
    homes, communities = await fetch_data()
    print(f"Total homes: {len(homes)} | Total communities: {len(communities)}")

    # Build community ID → community data map for Huntsville only
    huntsville_communities = {}
    for c in communities:
        slug = c.get('uniqueName', '').replace('-by-dsld-homes', '')
        if slug in HUNTSVILLE_SLUGS:
            huntsville_communities[c['_id']] = {**c, '_slug': slug}

    print(f"Huntsville communities matched: {len(huntsville_communities)}")

    # Filter homes to Huntsville + valid status
    huntsville_homes = [
        h for h in homes
        if h.get('containedIn') in huntsville_communities
        and h.get('status') in VALID_STATUSES
    ]
    print(f"Huntsville active homes: {len(huntsville_homes)}\n")

    inserted = updated = errors = 0

    for home in huntsville_homes:
        comm_data = huntsville_communities[home['containedIn']]
        comm_name = comm_data.get('name', '')
        comm_slug = comm_data.get('_slug', '')
        geo = comm_data.get('geoIndexed') or [None, None]
        lng, lat = geo[0], geo[1]

        community_id = get_or_create_community(comm_name, lng, lat, comm_slug)

        addr = home.get('address', {})
        street = (addr.get('streetAddress') or '').strip().title()
        city = addr.get('addressLocality', '').strip().title()
        if not street:
            continue

        # Update community city if blank
        supabase.table("communities").update({"city": city}).eq("id", community_id).eq("city", "").execute()

        baths_full = home.get('bathsFull') or 0
        baths_half = home.get('bathsHalf') or 0
        baths = baths_full + (0.5 * baths_half) if baths_half else float(baths_full)

        # Photos: use first photo, fall back to elevation photo
        image_url = None
        photos = home.get('photos') or []
        for p in photos:
            url = p.get('contentUrl') if isinstance(p, dict) else None
            if url:
                image_url = url
                break
        if not image_url:
            elev = home.get('elevationPhotos') or []
            for p in elev:
                url = p.get('contentUrl') if isinstance(p, dict) else None
                if url:
                    image_url = url
                    break

        listing = {
            "community_id": community_id,
            "address": street,
            "price": home.get('price'),
            "beds": home.get('beds'),
            "baths": baths,
            "garage": home.get('garages'),
            "sqft": home.get('sqft'),
            "stories": home.get('stories'),
            "image_url": image_url,
            "status": "available",
        }

        try:
            supabase.table("listings").insert(listing).execute()
            inserted += 1
            print(f"  ✓ {street} | {comm_name} | ${home.get('price'):,} | {home.get('beds')}bd/{baths}ba")
        except Exception as e:
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                supabase.table("listings").update({
                    k: v for k, v in listing.items() if k != "community_id"
                }).eq("address", street).execute()
                updated += 1
                print(f"  ~ updated {street}")
            else:
                print(f"  ✗ {street}: {e}")
                errors += 1

    print(f"\nDone! Inserted: {inserted} | Updated: {updated} | Errors: {errors}")


asyncio.run(main())