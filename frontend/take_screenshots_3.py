import asyncio
import json
from playwright.async_api import async_playwright

with open("mock.json", "r", encoding="utf-8") as f:
    MOCK_RESULT = json.load(f)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe", headless=True)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        # Intercept API calls
        async def handle_route(route):
            url = route.request.url
            if "/document/analyze-full" in url:
                await route.fulfill(status=200, json=MOCK_RESULT)
            elif "/auth/me" in url:
                await route.fulfill(status=200, json={"email": "test@test.com"})
            elif "images/placeholder" in url or "/images/" in url:
                 await route.continue_()
            else:
                await route.continue_()

        await page.route("**/*", handle_route)
        
        # Open page
        await page.goto("http://localhost:3000/dashboard")
        await page.wait_for_timeout(2000)
        
        # Take empty state
        await page.screenshot(path="evidence/ui_rebuild/01_dashboard_empty.png", full_page=True)
        print("01_dashboard_empty.png taken!")

        # Create a dummy file to upload
        with open("dummy.pdf", "w") as f:
            f.write("dummy")

        # Upload file
        await page.set_input_files("input[type='file']", "dummy.pdf")
        
        # Wait for form to appear and click analyze
        await page.wait_for_timeout(500)
        await page.click("button:has-text('Analiz Et')")
        
        # Wait for processing and layout to change
        await page.wait_for_timeout(3000)
        
        # Dashboard document loaded
        await page.screenshot(path="evidence/ui_rebuild/02_dashboard_document.png", full_page=True)
        print("02_dashboard_document.png taken!")
        
        await page.screenshot(path="evidence/ui_rebuild/03_three_panel_workspace.png")
        print("03_three_panel_workspace.png taken!")
        
        await browser.close()

asyncio.run(main())
