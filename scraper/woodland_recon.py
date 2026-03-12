import asyncio
import httpx
import json

BUILDER_ID = "572d8d4e371e2f345d9c64d2"

async def main():
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    async with httpx.AsyncClient() as client:
        homes_url = f'https://api.mybuildercloud.com/api/v1/homes?max_results=9999&where={{"isLot":{{"$ne":true}},"published":true,"builder":"{BUILDER_ID}"}}&projection={{"modifier_email":0,"creator_email":0}}'
        r1 = await client.get(homes_url, headers=headers, timeout=30)
        homes = r1.json().get("_items", [])

        comms_url = f'https://api.mybuildercloud.com/api/v1/communities?max_results=9999&where={{"published":true,"builder":"{BUILDER_ID}"}}&projection={{"modifier_email":0,"creator_email":0}}'
        r2 = await client.get(comms_url, headers=headers, timeout=30)
        communities = r2.json().get("_items", [])

    print(f"Total homes: {len(homes)} | Total communities: {len(communities)}")

    from collections import Counter
    statuses = Counter(h.get("status") for h in homes)
    print(f"Statuses: {dict(statuses)}")

    print("\nCommunities:")
    for c in communities:
        geo = c.get("geoIndexed") or []
        print(f"  {c.get('name')} | city={c.get('address',{}).get('addressLocality')} | geo={geo}")

    # Sample home
    active = [h for h in homes if h.get("status") == "Active" and not h.get("isModel")]
    print(f"\nActive non-model homes: {len(active)}")
    if active:
        h = active[0]
        photos = h.get("photos") or []
        print(f"  addr={h.get('address',{}).get('streetAddress')} | price={h.get('price')} | beds={h.get('beds')} | baths={h.get('bathsFull')} | sqft={h.get('sqft')}")
        print(f"  photos: {[p.get('contentUrl') for p in photos[:2]]}")

asyncio.run(main())