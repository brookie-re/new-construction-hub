import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})

        await page.goto("https://valorcommunities.lotvue.com/regions/HUNTSVILLE", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)

        link = await page.query_selector("a[href='#comm-anslee-farms']")
        if link:
            await link.click()
            await page.wait_for_timeout(5000)

        # Print counts from each section
        sections = await page.query_selector_all('[id^="comm-"]')
        print("Sections and counts:")
        for s in sections:
            sid = await s.get_attribute('id')
            text = await s.inner_text()
            count_m = __import__('re').search(r'(\d+) Available', text)
            print(f"  {sid}: {count_m.group(1) if count_m else '?'} listings")

        # Print first card full HTML
        cards = await page.query_selector_all('.inventory-list-item')
        print(f"\nTotal cards: {len(cards)}")
        first_html = await cards[0].inner_html()
        print(f"\nFirst card HTML:\n{first_html}")

        await browser.close()

asyncio.run(main())