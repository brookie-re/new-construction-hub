import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})

        async def handle_response(response):
            url = response.url
            if any(x in url for x in ['.css', '.png', '.jpg', '.woff', 'google', 'fonts', 'analytics', 'facebook']):
                return
            try:
                ct = response.headers.get("content-type", "")
                body = await response.text()
                if "json" in ct and len(body) > 200:
                    print(f"\nJSON URL: {url}")
                    print(f"Body: {body[:500]}")
            except:
                pass

        page.on("response", handle_response)

        await page.goto("https://www.legacyhomesal.com/communities/harvest-al/abbington", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(6000)

        for _ in range(5):
            await page.evaluate("window.scrollBy(0, 800)")
            await page.wait_for_timeout(800)

        html = await page.content()
        print(f"\nHTML length: {len(html)}")
        for term in ['__NEXT_DATA__', '__PRELOADED_STATE__', 'price', 'sqft', 'bedrooms']:
            if term in html:
                import re
                idx = html.find(term)
                print(f"\nFound '{term}' at {idx}:")
                print(repr(html[max(0,idx-50):idx+300]))

        await browser.close()

asyncio.run(main())