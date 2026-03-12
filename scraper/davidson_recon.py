import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})
        
        await page.goto("https://www.davidsonhomes.com/states/alabama/huntsville-market-area/athens/anderson-farm/", wait_until="networkidle")
        await page.wait_for_timeout(5000)
        
        # Scroll down and back up
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(3000)
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(2000)

        # Find article cards
        articles = await page.query_selector_all('article')
        print(f"Found {len(articles)} articles")
        
        for article in articles[:3]:
            text = await article.inner_text()
            print("\n--- ARTICLE ---")
            print(text[:400])

        await browser.close()

asyncio.run(main())