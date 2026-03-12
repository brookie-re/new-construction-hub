import asyncio
import httpx
import json

BUILDER_ID = "5702d467f410954eb27d1559"

async def main():
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    
    async with httpx.AsyncClient() as client:
        # Fetch all homes
        homes_url = f'https://api.mybuildercloud.com/api/v1/homes?max_results=9999&where={{"isLot":{{"$ne":true}},"published":true,"builder":"{BUILDER_ID}"}}&projection={{"modifier_email":0,"creator_email":0}}'
        r = await client.get(homes_url, headers=headers, timeout=30)
        homes = r.json().get("_items", [])
        print(f"Total homes: {len(homes)}")

        # Fetch all communities
        comms_url = f'https://api.mybuildercloud.com/api/v1/communities?max_results=9999&where={{"published":true,"builder":"{BUILDER_ID}"}}&projection={{"modifier_email":0,"creator_email":0}}'
        r2 = await client.get(comms_url, headers=headers, timeout=30)
        communities = r2.json().get("_items", [])
        print(f"Total communities: {len(communities)}")

    # Filter to Huntsville area communities
    huntsville_keywords = ["huntsville", "madison", "athens", "harvest", "toney", "meridianville", "hazel green", "new market", "moores mill"]
    huntsville_comms = {}
    for c in communities:
        name = c.get("name", "").lower()
        addr = json.dumps(c.get("address", {})).lower()
        if any(k in name or k in addr for k in huntsville_keywords):
            huntsville_comms[c["_id"]] = c
            print(f"  Community: {c.get('name')} | id={c['_id']} | geo={c.get('geoIndexed')}")

    print(f"\nHuntsville communities: {len(huntsville_comms)}")

    # Filter homes to Huntsville communities
    huntsville_homes = [h for h in homes if h.get("containedIn") in huntsville_comms]
    print(f"Huntsville homes: {len(huntsville_homes)}")

    # Status breakdown
    from collections import Counter
    statuses = Counter(h.get("status") for h in huntsville_homes)
    print(f"Statuses: {dict(statuses)}")

    # Sample home
    if huntsville_homes:
        h = huntsville_homes[0]
        print(f"\nSample home keys: {list(h.keys())}")
        print(f"addr={h.get('address',{}).get('streetAddress')} | price={h.get('price')} | beds={h.get('beds')} | baths={h.get('bathsFull')} | sqft={h.get('sqft')} | status={h.get('status')}")
        photos = h.get('photos', [])
        print(f"photos: {[p.get('contentUrl') for p in photos[:2]]}")

asyncio.run(main())