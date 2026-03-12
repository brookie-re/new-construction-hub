import asyncio
import httpx

async def main():
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    async with httpx.AsyncClient() as client:
        r = await client.get("https://www.stonemartinbuilders.com/find-my-home/meridianville/whitaker-landing", headers=headers, timeout=30)
        html = r.text

    # Count how many times "homes" appears
    count = html.count('\\"homes\\":[')
    print(f"Number of '\"homes\":' arrays: {count}")

    # Print context around each one
    start = 0
    for i in range(count):
        idx = html.find('\\"homes\\":[', start)
        print(f"\n--- Occurrence {i+1} at index {idx} ---")
        # Print 100 chars before to see what object this belongs to
        print(repr(html[max(0,idx-150):idx+50]))
        start = idx + 1

asyncio.run(main())