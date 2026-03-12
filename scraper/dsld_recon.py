import asyncio
import httpx
import json

async def main():
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    async with httpx.AsyncClient() as client:
        r = await client.get("https://www.dsldhomes.com/communities/alabama/huntsville/kennesaw-creek", headers=headers, timeout=30)
        html = r.text

    idx = html.find('window.__PRELOADED_STATE__ = ')
    start = idx + len('window.__PRELOADED_STATE__ = ')
    end = html.find('</script>', start)
    data = json.loads(html[start:end].strip().rstrip(';'))

    BUILDER_ID = '5702af75f410954eb27ce27a'
    cloud = data['cloudData']
    homes = cloud['homes'][BUILDER_ID]['data']
    communities = cloud['communities'][BUILDER_ID]['data']

    print(f"Homes: {len(homes)}, Communities: {len(communities)}")

    if homes:
        h = homes[0]
        print(f"\nHome keys: {list(h.keys())}")
        print(f"addr={h.get('address',{}).get('streetAddress')} | city={h.get('address',{}).get('addressLocality')} | price={h.get('price')} | status={h.get('status')} | beds={h.get('beds')} | baths={h.get('bathsFull')} | sqft={h.get('sqft')} | garage={h.get('garages')}")
        print(f"photos: {[p.get('contentUrl') for p in h.get('photos',[])[:2]]}")

    if communities:
        c = communities[0]
        print(f"\nCommunity keys: {list(c.keys())[:10]}")
        print(f"name={c.get('name')} | uniqueName={c.get('uniqueName')} | geo={c.get('geoIndexed')}")

asyncio.run(main())