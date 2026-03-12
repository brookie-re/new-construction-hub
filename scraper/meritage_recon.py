import asyncio
from urllib.parse import unquote
import re
from playwright.async_api import async_playwright

COMMUNITY_PAGES = [
    "https://www.meritagehomes.com/state/al/huntsville/walkers-hill",
    "https://www.meritagehomes.com/state/al/huntsville/kendall-farms",
    "https://www.meritagehomes.com/state/al/huntsville/madison-preserve-the-reserve-series",
    "https://www.meritagehomes.com/state/al/huntsville/madison-preserve-the-estate-series",
]

async def get_images_for_page(page, url):
    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_timeout(6000)
    for _ in range(5):
        await page.evaluate("window.scrollBy(0, 800)")
        await page.wait_for_timeout(600)

    images = await page.evaluate("""() => {
        const results = [];
        document.querySelectorAll('img').forEach(img => {
            if (img.alt && img.src && img.src.includes('sitecorecontenthub')) {
                results.push({ alt: img.alt.trim(), src: img.src });
            }
        });
        return results;
    }""")
    return images

async def main():
    address_to_image = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for url in COMMUNITY_PAGES:
            print(f"\nScraping: {url}")
            images = await get_images_for_page(page, url)
            for img in images:
                alt = img['alt'].lower()
                # Extract the real content hub URL from Next.js proxy
                m = re.search(r'url=(https[^&]+)', img['src'])
                if m:
                    real_url = unquote(m.group(1))
                    # Normalize address: title case, strip extra spaces
                    addr = img['alt'].strip().title()
                    if addr not in address_to_image:
                        address_to_image[addr] = real_url
                        print(f"  {addr} → {real_url[:80]}")

        await browser.close()

    print(f"\nTotal address→image mappings: {len(address_to_image)}")

asyncio.run(main())