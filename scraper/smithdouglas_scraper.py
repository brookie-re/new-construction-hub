import asyncio
import httpx
import json
from typing import Optional
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
BUILDER = "Smith Douglas Homes"
BUILDER_ID = "5702d467f410954eb27d1559"

VALID_STATUSES = {"Active"}

HUNTSVILLE_KEYWORDS = [
    "huntsville", "madison", "athens", "harvest", "toney",
    "meridianville", "hazel green", "new market", "moores mill",
    "limestone", "decatur"
]


def get_or_create_community(c: dict) -> int:
    name = c.get("name", "")
    existing = supabase.table("communities").select("id").eq("name", name).eq("builder", BUILDER).execute()
    if existing.data:
        return existing.data[0]["id"]

    geo = c.get("geoIndexed") or [None, None]
    addr = c.get("address", {})
    city = addr.get("addressLocality", "")
    slug = c.get("uniqueName", "").replace("-by-smith-douglas-homes", "")

    result = supabase.table("communities").insert({
        "name": name,
        "builder": BUILDER,
        "city": city,
        "state": "AL",
        "latitude": geo[1] if geo[1] else None,
        "longitude": geo[0] if geo[0] else None,
        "website_url": f"https://www.smithdouglas.com/communities/huntsville-al/{slug}",
    }).execute()
    print(f"  Created community: {name}")
    return result.data[0]["id"]


async def fetch_data():
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    async with httpx.AsyncClient() as client:
        homes_url = f'https://api.mybuildercloud.com/api/v1/homes?max_results=9999&where={{"isLot":{{"$ne":true}},"published":true,"builder":"{BUILDER_ID}"}}&projection={{"modifier_email":0,"creator_email":0}}'
        r1 = await client.get(homes_url, headers=headers, timeout=30)
        homes = r1.json().get("_items", [])

        comms_url = f'https://api.mybuildercloud.com/api/v1/communities?max_results=9999&where={{"published":true,"builder":"{BUILDER_ID}"}}&projection={{"modifier_email":0,"creator_email":0}}'
        r2 = await client.get(comms_url, headers=headers, timeout=30)
        communities = r2.json().get("_items", [])

    return homes, communities


async def main():
    print("Fetching Smith Douglas data...")
    homes, communities = await fetch_data()
    print(f"Total homes: {len(homes)} | Total communities: {len(communities)}")

    # Filter to Huntsville communities
    huntsville_comms = {}
    for c in communities:
        name = c.get("name", "").lower()
        addr = json.dumps(c.get("address", {})).lower()
        if any(k in name or k in addr for k in HUNTSVILLE_KEYWORDS):
            huntsville_comms[c["_id"]] = c

    print(f"Huntsville communities: {len(huntsville_comms)}")

    # Filter homes
    huntsville_homes = [
        h for h in homes
        if h.get("containedIn") in huntsville_comms
        and h.get("status") in VALID_STATUSES
    ]
    print(f"Huntsville active homes: {len(huntsville_homes)}\n")

    inserted = updated = errors = 0

    for home in huntsville_homes:
        comm = huntsville_comms[home["containedIn"]]
        community_id = get_or_create_community(comm)

        addr = home.get("address", {})
        street = (addr.get("streetAddress") or "").strip().title()
        if not street:
            continue

        baths_full = home.get("bathsFull") or 0
        baths_half = home.get("bathsHalf") or 0
        baths = float(baths_full) + (0.5 * float(baths_half) if baths_half else 0)

        # Get first photo
        image_url = None
        for p in (home.get("photos") or []):
            url = p.get("contentUrl") if isinstance(p, dict) else None
            if url:
                image_url = url
                break
        if not image_url:
            for p in (home.get("elevationPhotos") or []):
                url = p.get("contentUrl") if isinstance(p, dict) else None
                if url:
                    image_url = url
                    break

        listing = {
            "community_id": community_id,
            "address": street,
            "price": home.get("price"),
            "beds": home.get("beds"),
            "baths": baths or None,
            "garage": home.get("garages"),
            "sqft": home.get("sqft"),
            "stories": home.get("stories"),
            "image_url": image_url,
            "status": "available",
        }

        price_str = f"${listing['price']:,}" if listing["price"] else "N/A"

        try:
            supabase.table("listings").insert(listing).execute()
            inserted += 1
            print(f"  ✓ {street} | {comm.get('name')} | {price_str} | {listing['beds']}bd/{listing['baths']}ba")
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