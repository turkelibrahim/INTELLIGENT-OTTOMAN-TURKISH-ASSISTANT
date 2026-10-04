import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe", headless=True)
        page = await browser.new_page()
        await page.goto("http://localhost:3000/dashboard")
        await page.wait_for_timeout(5000) # Wait 5s for page to load completely
        await page.screenshot(path="evidence/ui_rebuild/current_dashboard_after_rebuild.png", full_page=True)
        print("Screenshot taken!")
        await browser.close()

asyncio.run(main())
