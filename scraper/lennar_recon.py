import asyncio
from playwright.async_api import async_playwright

async def recon():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Visiting Lennar St. Clair Place...")
        await page.goto("https://www.lennar.com/new-homes/alabama/huntsville/huntsville/st-clair-place", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(4000)

        await page.screenshot(path="lennar_page.png", full_page=True)
        print("Screenshot saved!")

        title = await page.title()
        print(f"Page title: {title}")

        await browser.close()

asyncio.run(recon())