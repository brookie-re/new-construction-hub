import asyncio
import httpx
import re
import json
from typing import Optional
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
BUILDER = "Stone Martin Builders"

COMMUNITY_META = {
    "Parvin Preserve":             ("Meridianville",     "meridianville",      "parvin-preserve",               34.8738, -86.5228),
    "Whitaker Landing":            ("Meridianville",     "meridianville",      "whitaker-landing",              34.8701, -86.5310),
    "Magnolia Hill":               ("Toney",             "toney",              "magnolia-hill",                 34.9163, -86.6761),
    "Nature's Trail":              ("Madison",           "madison",            "natures-trail",                 34.7273, -86.7483),
    "Nature's Walk on the Flint":  ("Owens Cross Roads", "owens-cross-roads",  "natures-walk-on-the-flint",     34.6121, -86.4962),
    "Oak Meadows":                 ("Owens Cross Roads", "owens-cross-roads",  "oak-meadows",                   34.6018, -86.4901),
    "Swan Woods":                  ("Athens",            "athens",             "swan-woods",                    34.8021, -86.9583),
    "The Preserve at Inspiration": ("Huntsville",        "huntsville",         "the-preserve-at-inspiration",   34.6581, -86.5744),
    "Town Madison":                ("Madison",           "madison",            "town-madison",                  34.6993, -86.7483),
}

VALID_STATUSES = {"Move-in Ready", "Available for Sale"}


def parse_garage(garage_type: Optional[str]) -> Optional[int]:
    if not garage_type:
        return None
    m = re.search(r'(\d+)', garage_type)
    if m:
        return int(m.group(1))
    if "j-drive" in garage_type.lower():
        return 2
    return None


def get_or_create_community(title: str, lng: Optional[float], lat: Optional[float]) -> int:
    existing = supabase.table("communities").select("id").eq("name", title).eq("builder", BUILDER).execute()
    if existing.data:
        return existing.data[0]["id"]
    meta = COMMUNITY_META.get(title)
    city, loc_slug, comm_slug, fallback_lat, fallback_lng = meta if meta else ("Huntsville", "", "", None, None)
    result = supabase.table("communities").insert({
        "name": title,
        "builder": BUILDER,
        "city": city,
        "state": "AL",
        "latitude": lat if lat is not None else fallback_lat,
        "longitude": lng if lng is not None else fallback_lng,
        "website_url": f"https://www.stonemartinbuilders.com/find-my-home/{loc_slug}/{comm_slug}",
    }).execute()
    print(f"  Created community: {title}")
    return result.data[0]["id"]


def extract_homes_from_html(html: str) -> list:
    all_homes = {}
    start = 0
    while True:
        idx = html.find('\\"homes\\":[', start)
        if idx == -1:
            break
        arr_start = idx + len('\\"homes\\":')
        
        # Skip if this array contains IDs only (not full objects)
        peek = html[arr_start:arr_start+10]
        if not (peek.startswith('[{\\"') or peek.startswith('[{ \\"')):
            start = idx + 1
            continue

        # Walk brackets to find end of array
        depth = 0
        end = arr_start
        for i, ch in enumerate(html[arr_start:], arr_start):
            if ch == '[':
                depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break

        try:
            raw = html[arr_start:end].replace('\\"', '"').replace('\\\\', '\\')
            homes = json.loads(raw)
            for h in homes:
                addr = h.get("streetAddress", "")
                if addr and isinstance(h, dict) and h.get("community"):
                    all_homes[addr] = h
        except Exception:
            pass

        start = idx + 1

    return list(all_homes.values())


async def main():
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    inserted = updated = errors = 0

    async with httpx.AsyncClient() as client:
        all_homes = {}  # address → home, deduped across pages

        for community_name, meta in COMMUNITY_META.items():
            _, loc_slug, comm_slug, _, _ = meta
            url = f"https://www.stonemartinbuilders.com/find-my-home/{loc_slug}/{comm_slug}"
            r = await client.get(url, headers=headers, timeout=30)
            homes = extract_homes_from_html(r.text)
            # Only keep homes matching this community
            for h in homes:
                if h.get("community", {}).get("title") == community_name:
                    addr = h.get("streetAddress", "")
                    if addr:
                        all_homes[addr] = h
            print(f"  Fetched {community_name}: {len([h for h in homes if h.get('community',{}).get('title')==community_name])} homes")

    all_homes = list(all_homes.values())
    print(f"\nTotal unique Huntsville homes: {len(all_homes)}")

    print(f"Total homes parsed from page: {len(all_homes)}")

    for community_name in COMMUNITY_META:
        print(f"\n{community_name}:")

        # Filter to this community and valid statuses only
        community_homes = [
            h for h in all_homes
            if h.get("community", {}).get("title") == community_name
            and h.get("status") in VALID_STATUSES
        ]
        print(f"  {len(community_homes)} homes")

        for home in community_homes:
            loc = home.get("location") or [None, None]
            community_id = get_or_create_community(community_name, loc[0], loc[1] if len(loc) > 1 else None)

            fp = home.get("floorPlan") or {}
            address = (home.get("streetAddress") or "").strip()
            if not address:
                continue

            image_url = None
            for p_item in (home.get("photos") or []):
                if isinstance(p_item, dict):
                    photo = p_item.get("photo")
                    if isinstance(photo, dict) and photo.get("url"):
                        image_url = photo["url"].replace(" ", "%20")
                        break
            if not image_url:
                cfp = home.get("communityFloorPlan") or {}
                for source in [cfp.get("communityFloorplanPhotos"), cfp.get("photos"), fp.get("photos")]:
                    for p_item in (source or []):
                        if isinstance(p_item, dict):
                            photo = p_item.get("photo") or p_item
                            if isinstance(photo, dict) and photo.get("url"):
                                image_url = photo["url"].replace(" ", "%20")
                                break
                    if image_url:
                        break

            listing = {
                "community_id": community_id,
                "address": address,
                "price": home.get("price"),
                "beds": fp.get("bedCount"),
                "baths": fp.get("bathCount"),
                "garage": parse_garage(home.get("garageType")),
                "sqft": home.get("squareFootage"),
                "image_url": image_url,
                "status": "available",
            }

            try:
                supabase.table("listings").insert(listing).execute()
                inserted += 1
                print(f"  ✓ {address} | ${home.get('price'):,} | {fp.get('bedCount')}bd/{fp.get('bathCount')}ba | {home.get('status')}")
            except Exception as e:
                if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                    supabase.table("listings").update({k: v for k, v in listing.items() if k != "community_id"}).eq("address", address).execute()
                    updated += 1
                    print(f"  ~ updated {address}")
                else:
                    print(f"  ✗ {address}: {e}")
                    errors += 1

    print(f"\nDone! Inserted: {inserted} | Updated: {updated} | Errors: {errors}")


asyncio.run(main())