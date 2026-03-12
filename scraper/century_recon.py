import asyncio
from playwright.async_api import async_playwright
import re

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})

        await page.goto("https://www.centurycommunities.com/find-your-new-home/alabama/huntsville-metro/toney/kendall-glades/", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(6000)
        for _ in range(5):
            await page.evaluate("window.scrollBy(0, 800)")
            await page.wait_for_timeout(800)

        # Use JS to extract card data directly from the DOM
        cards = await page.evaluate("""() => {
            const results = [];
            document.querySelectorAll('li[data-price]').forEach(li => {
                results.push({
                    price: li.dataset.price,
                    sqft: li.dataset.sqft,
                    address: (li.querySelector('.street-number-text') || {}).innerText || '',
                    href: (li.querySelector('a[href*="/lots/"]') || {}).href || '',
                    beds: (li.querySelector('img[alt="Bedrooms"]')?.parentElement || {}).innerText || '',
                    baths: (li.querySelector('img[alt="Bathrooms"]')?.parentElement || {}).innerText || '',
                    garages: (li.querySelector('img[alt="Garage"]')?.parentElement || {}).innerText || '',
                    imgId: li.querySelector('[id^="quick-move-in-gallery-"]')?.id || '',
                    fullText: li.innerText.slice(0, 500),
                });
            });
            return results;
        }""")

        await browser.close()

    print(f"Cards: {len(cards)}")
    for c in cards[:3]:
        print(f"\n{c}")

asyncio.run(main())